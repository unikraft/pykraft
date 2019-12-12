#!/usr/bin/env python3
# Kraft 'fetch' command implementation

########### Imports #############
import os, sys
from  config import *
import utils

########### Globals #############
# Get the sub-command from the user
sub_cmd = sys.argv[1]

########### Functions ###########

# Create the unikraft src directory structure
utils.create_dir(os.path.join(UK_BASE_SRC,UK_APPS_DIR), \
                 os.path.join(UK_BASE_SRC,UK_LIBS_DIR), \
                 os.path.join(UK_BASE_SRC,UK_PLATS_DIR) \
                )






