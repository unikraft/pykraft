#!/usr/bin/env python3
# Kraft 'fetch' command implementation

########### Imports #############
import os, sys
from config import *
import utils
import requests
import json

########### Globals #############
# Get the sub-command(App name) from the user
app_name = sys.argv[1]

########### Functions ###########
# Check if already cloned
def is_git_repo(path):
     if os.path.exists(path+'/.git'):
        print(path+": Already a git repo! You might wanna run 'update' command")
        return True
     else:
        return False

# Create the base src directory
utils.create_dir(UK_BASE_SRC)
#Change current dir to base src
os.chdir(UK_BASE_SRC)
# Create the unikraft src directory structure
utils.create_uk_dirs()
# Clone the app repo
CLONE = utils.create_url(UK_APPS_DIR,app_name)
if not is_git_repo('apps/'+app_name):
    os.system(CLONE+" "+UK_APPS_DIR+"/"+app_name)
# Get the deps.json file path for given 'app'
deps = UK_APPS_DIR+'/'+app_name+'/'+DEPS_JSON_FILE
if os.path.exists(deps):
    with open(UK_APPS_DIR+'/'+app_name+'/'+DEPS_JSON_FILE) as f:
        app_deps = json.load(f)
else:
    print('----------------------------------------')
    print('\033[1m' + 'Error:' + '\033[0m')
    print('\033[1m' + app_name + '\033[0m'+': App dependency file '+'\033[1m' + '(deps.json)' + '\033[0m'+ ' not found. Try cleaning the src directory and rerun the command.')
    print('Exiting!')
    exit()

# Fetches all the repos mentioned under 'core' section of the deps.json file
def fetch_core_deps(core_dep):
    for k,v in core_dep.items():
        if not is_git_repo(str(k)):
            clone = utils.create_url(UK_CORE_DIR,str(k)) + TO_BLACK_HOLE
            os.system(clone)

# Fetches all the repos mentioned under 'libs' section of the deps.json file
def fetch_lib_deps(lib_dep):
    for k,v in lib_dep.items():
        if not is_git_repo('libs/'+str(k)):
            clone = utils.create_url(UK_LIBS_DIR,str(k))+" "+ UK_LIBS_DIR+'/'+str(k)
            os.system(clone)

# Fetches all the repos mentioned under 'plats' section of the deps.json file
def fetch_plat_deps(plat_dep):
    for k,v in plat_dep.items():
        if not is_git_repo('plats/'+str(k)):
            clone = utils.create_url(UK_LIBS_DIR,str(k))+" "+ UK_PLATS_DIR+'/'+str(k)
            os.system(clone)

# Fetches all the repos mentioned in deps.json file
def fetch_deps(deps):
  for k,v in deps.items():
     if k == 'core':
        fetch_core_deps(v)
     elif k == 'libs':
        fetch_lib_deps(v)
     elif k == 'plats':
        fetch_plat_deps(v)
     else:
        print('Invalid Key')

# Fetches all the dependencies required for a given 'app'
fetch_deps(app_deps)





