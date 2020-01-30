#!/usr/bin/env python3
# Kraft 'configure' command implementation

########### Imports #############
import os, sys
from  config import *
import utils

########### Globals #############
# Get the sub-command from the user
app_name = sys.argv[1]

########### Functions ###########

os.chdir(UK_BASE_SRC+'/'+UK_APPS_DIR+"/"+app_name)
os.system('make defconfig')




