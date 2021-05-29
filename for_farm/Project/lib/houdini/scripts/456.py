import hou
base=hou.getenv("BASEJOB")

if base!=None:
    hou.putenv('JOB',base)
    hou.hscript("JOB "+base)
    hou.hscript("varchange JOB")
    hou.allowEnvironmentToOverwriteVariable("JOB", True)