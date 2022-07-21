from __future__ import print_function
import multiprocessing 
import hou, ftplib, os, time, glob, subprocess
import os,glob
from PySide2 import QtWidgets, QtCore, QtGui

##############################
##########list files in JOB
jobdir = hou.getenv("JOB")

def checker():
    tmpparms=[]
    nodes=hou.node('/').allSubChildren()
    for n in nodes:
        try:
            a=n.type().definition()
            if 'job_replace' in a.nodeTypeName():
                b=n.parm('jpath')
                if not b.isAtDefault():
                    tmpparms.append(b)
        except:
            pass
    if len(tmpparms)!=0:    
        answer=hou.ui.displayMessage('JobReplaceAsset not in Default!!! Correct it?', buttons=('Yes','No') , severity=hou.severityType.Message, default_choice=1, close_choice=1,help='', details='', details_label="JobReplace")
        if answer==0:
            for parm in tmpparms:
                try:
                    parm.revertToDefaults()
                except:
                    pass
      


def givemefiles(files,scena,jobdir='',excludes=[]):
    dirs=[]
    fileslist=[]
    for f in files:
        try:
            if jobdir in f:
                if os.path.isfile(f):
                    dir=os.path.dirname(f)
                    dirs.append(dir)
                else:
                    if os.path.exists(f):
                        dir=f
                        dirs.append(dir) 
        except:
            pass
        udirs=sorted(set(dirs))
        #print(udirs)
    for d in udirs:             
        try:
            tmp=os.chdir(os.path.normpath(d))
            newtmp=glob.glob('*.*')
            fileslist+=[os.path.abspath(x) for x in newtmp]
        except:
            pass
            
    fileslist=sorted(set(fileslist))
    newfiles=[]

    for n in fileslist:
        #n=n.replace('\\','/')
        if os.path.isfile(n):
            if os.path.isdir(n)!=True:
                if len(excludes)>0:
                    a=1
                    for k in excludes:
                        if k in n:
                            a=0
                            break
                    if a==1:
                        n=n.replace('\\','/')
                        n=n.replace(jobdir,'')
                        n=os.path.normpath(n)
                        newfiles.append(n)
                else:
                    n=n.replace('\\','/')
                    n=n.replace(jobdir,'')
                    n=os.path.normpath(n)
                    newfiles.append(n)
    return newfiles

def colfileslist(jobdir,ans=0,exclude=[]):
    excl=exclude
#    answer=hou.ui.displayMessage('CHECK SEQUENCES ?', buttons=('Yes','No') , severity=hou.severityType.Message, default_choice=1, #close_choice=1,help='', details='', details_label="Collect Sequences")
    scena=hou.getenv('HIPFILE')
    dirs_scena=[]
    dirs_scena=[x[0].replace('\\','/') for x in os.walk(os.path.normpath(os.path.dirname(scena)))]
    
    scenafiles=[]
    tmpfiles=[]
    scenaarr=[]
    if jobdir in scena:
        curscena=scena.replace(jobdir,'')
        scenaarr.append(curscena)

    scn=list(scenaarr)
    if ans>3:
        answer=hou.ui.displayMessage('What to send?', buttons=('Only Scena','All in Job Reference','HIP_Dir','AllFiles in Job') , severity=hou.severityType.Message, default_choice=0, close_choice=4,help='', details='', details_label="Send Scena")
    else:
        answer=ans
        
    if answer==0:
        #checker()
        out=scn
        
    elif answer==1:
        #checker()
        try:
            scenafiles=list(givemefiles(dirs_scena,scena,jobdir,excl))
        except:
            pass
        out=scenafiles
        
    elif answer==2:
        #checker()    
        pack=hou.fileReferences("JOB")
        for parm, path in pack:
            file=hou.expandString(path)
            file=file.replace('\\','/')
                ##file=file.replace(jobdir,'')
            tmpfiles.append(file)



        scenafiles=list(givemefiles(tmpfiles+dirs_scena,scena,jobdir,excl))
        scenafiles.sort()
    
        out=scenafiles
        
    elif answer==3:
        #checker()
        jb=jobdir
        tmpfiles=[]
        for f in glob.glob(jb+'/**/*.*', recursive=True):
            file=f.replace('\\','/')
            tmpfiles.append(file)
        scenafiles=list(givemefiles(tmpfiles+dirs_scena,scena,jobdir,excl))


            
        scenafiles.sort()
    
        out=scenafiles
    return out
############################
########Uploading
def uploadfiles(host,files,project,jobdir,login=[]):
    result=0
    hou.putenv('FARMSTOP','0')
    stopper='0'
    ##########GUI
    stylesheet = ("""
            QProgressBar {
                    border: 1px solid grey;
                    background-color: #3a3a3a;
                    border-radius: 0px;
                    text-align: center;
                    margin: 3 px;
                    }
    
                    QProgressBar::chunk {
                    background-color: #e6c63c;
                    width: 20px;
                            }
            """)
    num_textures = len(files)
    bar = QtWidgets.QProgressBar()
    bar.setWindowTitle('send to farm...')
    x = QtWidgets.QDesktopWidget().screenGeometry().center().x()
    y = QtWidgets.QDesktopWidget().screenGeometry().center().y()
    width = 800
    height = 50

    bar.setGeometry( x - (width * 0.5),y - (height * 0.5) , width, height)
    bar.setValue( 0 )
    bar.setStyleSheet(stylesheet)

    bar.show()
    bar.activateWindow()
    QtWidgets.QApplication.processEvents()
    time.sleep(.2)
    rc=0
    
    
############
    try:
        if len(login)>=2:
            ftp = ftplib.FTP(host,login[0],login[1],acct='', timeout=35)
            #ftp.cwd('/'+project+'/')
            hou.putenv('FARMSTOP','0')
            for file in files:
                try:
                    hou.getenv('FARMSTOP')
                except:
                    pass
                if not bar.isHidden():
                    QtWidgets.QApplication.processEvents()
                
                    if file.endswith('.hda') or file.endswith('.otl'):
                        isasset=True
                    else:
                        isasset=False
                    ftpfile='/Projects/'+project+file.replace('\\','/')
                    #print("----------------------------------")
                    #print(ftpfile)
    
                    dircnt=file.split('/')
                    file_name = dircnt[len(dircnt)-1]
                    localfile=jobdir+file
                    bar.setWindowTitle('send to farm: '+file_name)
                    fpath=ftpfile.replace(ftpfile.split('/')[-1],'')
                    try:
                        sizef=ftp.size(ftpfile)
                        localsize=os.path.getsize(localfile)
                        if sizef!=localsize:
                            try:
                                ftp.cwd(fpath)
                                tosend=open(localfile, 'rb')
                                ftp.storbinary('STOR ' + ftpfile, tosend)
                                tosend.close()
                            except:
                                "error:not overrided!!"
                        else:
                            pass
                    except:
    ####
                        try:
                            try:
                                ftp.cwd(fpath)
                                tosend=open(localfile, 'rb')
                                ftp.storbinary('STOR ' + ftpfile, tosend)
                                tosend.close()
                            except:
                                dirs=fpath.split('/')
                                del dirs[0]
                                del dirs[-1]
                                temppath=''
                                for dir in dirs:
                                    temppath+='/'+dir
                                    try:
                                        ftp.cwd(temppath)
                                    except:
                                        ftp.mkd(temppath)
                                ftp.cwd(fpath)
                                tosend=open(localfile, 'rb')
                                ftp.storbinary('STOR ' + ftpfile, tosend) 
                                tosend.close()
                        except:
                            print( 'upload error: '+fpath)
    ######progress bar
                    rc = rc + 1
                
        
                    progress = (float(rc)/float(num_textures)) * 100
        
                    bar.setValue( progress )
                    ##time.sleep(.1)
    
                else:
                    break
                    result=1
                    hou.putenv('FARMSTOP','0')
    ######
            ftp.quit()
            bar.close()
        else:
            result=1
            print("Incorrect login and password!")
    except Exception as e:
        result=1
        print(e)
    return result
 ###RUN
####uploadfiles(host,fileslist(jobdir),project,jobdir)
