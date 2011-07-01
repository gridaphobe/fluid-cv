from fabric.api import local

def test():
    local("python test_fluidcv.py")

def commit():
    local("git add -p && git commit")

def deploy():
    test()
    commit()
    local("$HOME/Source/google_appengine/appcfg.py update .")

def server():
    local("$HOME/Source/google_appengine/dev_appserver.py -p 3000 .")
