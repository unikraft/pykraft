#!/usr/bin/env python3
# Kraft 'fetch' command implementation

########### Imports #############
import os, sys
from config import *

########### Globals #############
# Get the sub-command(App name) from the user
git_tag = sys.argv[1]

########### Functions ###########

def do_pull(repo):
    pull = GIT+' -C '+repo+' pull'
    print('git pull '+repo)
    os.system(pull)

# Iterate over all the repos and do pull
for subdir, dirs, files in os.walk(UK_BASE_SRC):
    for d in dirs:
        if d == '.git':
            do_pull(subdir)

