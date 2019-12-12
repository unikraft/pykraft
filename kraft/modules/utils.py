#!/usr/bin/env python3
# This file contains util methods required by 'core kraft' system
import sys
import os
import config

# ERROR/INFO CODES
SUCCESS = True
FAILURE = False
DIR_ALREADY_EXISTS = -1
FILE_ALREADY_EXISTS = -2

# This method executes the given sub-command
def invoke_sub_cmd(cmd, sub_cmd):
    os.system(sys.executable+" "+os.path.join(config.CMD_DIR, cmd)+".py"+" "+sub_cmd)

# Creates given directory(s).
def create_dir(*dirs):
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)

