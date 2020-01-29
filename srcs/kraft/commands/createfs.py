#!/usr/bin/env python3
# Kraft 'createfs' command implementation

########### Imports #############
import sys
from  config import *
import utils
import tarfile
########### Globals #############
# Get the sub-command from the user
fs_type = sys.argv[1]

########### Functions ###########

#Change current dir to base src
os.chdir(UK_BASE_SRC)
fs_path = UK_APPS_DIR +'/'+ fs_type
tf = tarfile.open(fs_path+'/'+UK_PY_FS)
tf.extractall()




