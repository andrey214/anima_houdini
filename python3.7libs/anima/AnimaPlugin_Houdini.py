hou_info = {
    'name': 'Animarender Plugin',
    'description': 'Plugin for submit scene to animarender farm',
    'author': 'Andrey Ek',
    'version': (0, 0, 1),
    'houdini': (18, 5, 351),
    'location': 'Render -> Render with Anima',
    'warning': '',
    'doc_url': '',
    'tracker_url': '',
    'category': 'Render'
}
import os
import re
import sys
import json
import errno
import socket
import locale
import shutil
import logging
import tempfile
import textwrap
import traceback
from io import StringIO
from time import sleep
try:
    import hou
    ver=hou.applicationVersionString().split('.')
    hou_info['houdini']=(ver[0],ver[1],ver[2])
except:
    pass

import builtins as __builtin__

RU = 'ru'
EN = 'en'
LOCALES = {}
LOCALES[EN] = 0
LOCALES[RU] = 1

try:
    filepath = os.path.join(tempfile.gettempdir(), 'AnimaPlugin.json')
except:
    filepath = ''

active_locale = EN






SOCK_OLD_PORT = 1337
SOCK_NEW_PORT = 43546

LOG_PATH = os.path.join(tempfile.gettempdir(), 'AnimaPluginLogs.log')
logging.basicConfig(
    filename=LOG_PATH,
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s — %(name)s — %(levelname)s — %(funcName)s: line %(lineno)d — %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)

print('AnimaPlugin log path: {}'.format(LOG_PATH))

ready_to_submit = True


# UTILS
class Sock:
    @staticmethod
    def parse_response(response):
        try:
            response = response.decode('utf-8')
            logging.info('Response was decoded and parsed successfully, response = %s', str(response))
            return json.loads(response)
        except:
            logging.exception('Parse response err: \n response = %s', response)
            return None

    @staticmethod
    def send(data, timeout=None, port=None):
        address = ('localhost', port or SOCK_NEW_PORT)
        response = b''

        logging.info('Request to socket, data = %s', str(data))
        try:
            sock = socket.socket()
            sock.settimeout(timeout or 10)
            sock.connect(address)
            logging.info('Connection to socket to address = %s', str(address))
            data = json.dumps(data)
            sock.send(data.encode('utf-8'))
            tmp = sock.recv(1024)
            while tmp:
                response += tmp
                tmp = sock.recv(1024)
        except Exception as e:
            logging.exception('Socket error %s', str(port))
            if e.errno in (errno.ECONNREFUSED, 10061) and port != SOCK_OLD_PORT:
                return Sock.send(data, timeout, SOCK_OLD_PORT)
            return False, response
        finally:
            sock.close()

        parsed_response = Sock.parse_response(response)
        logging.info('Sock response: %s', str(parsed_response))

        # If response not valid try resend msg to old port
        if (port != SOCK_OLD_PORT and (parsed_response is None
                                       or (isinstance(parsed_response, dict) and not parsed_response.get('action',
                                                                                                         None)))):
            logging.info('Response is not valid, trying to resend msg to old port')
            return Sock.send(data, timeout, SOCK_OLD_PORT)
        return True, parsed_response

    @staticmethod
    def check_manager():
        # Check connect to AM
        data = {
            'action': 'plugin',
            'params': {
                'name': 'Houdini',
                'version': hou_info['houdini'],
            }
        }
        logging.info('Checking connection with AnimaManager, data = %s', str(data))
        return Sock.send(data)

    @staticmethod
    def submit_job(params):
        data = {
            'action': 'submit',
            'params': params,
        }
        return Sock.send(data, timeout=60)

    @staticmethod
    def submit_err(e_message):
        data = {
            'action': 'err',
            'params': {
                'software': 'Houdini ' + hou_info['houdini'],
                'plugin': '.'.join(map(str, hou_info['version'])),
                'message': e_message
            },
        }
        return Sock.send(data, timeout=45)



if __name__ == '__main__':
    register()
