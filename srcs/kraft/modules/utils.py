#!/usr/bin/env python3
# This file contains util methods required by 'core kraft' system
import sys
import os, subprocess
from config import *
from subprocess import call, STDOUT

# ERROR/INFO CODES
SUCCESS = True
FAILURE = False
DIR_ALREADY_EXISTS = -1
FILE_ALREADY_EXISTS = -2

# This method executes the given sub-command
def invoke_sub_cmd(cmd, sub_cmd):
    os.system(sys.executable+" "+os.path.join(CMD_DIR, cmd)+".py"+" "+sub_cmd)

# Creates given directory(s).
def create_dir(*dirs):
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)

# Creates unikraft directory structure
def create_uk_dirs():
    create_dir( UK_APPS_DIR, UK_LIBS_DIR, UK_PLATS_DIR )

def create_url(repo_type, name):
    if repo_type == UK_CORE_DIR:
        repo_url = CORE_REPO_URL
    elif repo_type == UK_APPS_DIR:
        repo_url = APPS_REPO_URL
    elif repo_type == UK_LIBS_DIR:
        repo_url = LIBS_REPO_URL
    else:
        repo_url = PLATS_REPO_URL

    #git_clone = CLONE +" "+ repo_url
    clone = CLONE +" "+ repo_url + name + '.git'
    return clone


def check_git_repo(path):
    if os.path.exists(path+'/.git'):
        return True
    else:
        return False
    '''
    if call(["git", "branch"], stderr=STDOUT, stdout=open(os.devnull, 'w')) != 0:
        return False
    else:
        return True
    '''
def is_git_directory(path = '.'):
    if subprocess.call(['git', '-C', path, 'status'], stderr=subprocess.STDOUT, stdout = open(os.devnull, 'w')) == 0:
        return True
    else:
        return False
