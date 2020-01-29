#!/usr/bin/env python3
# Kraft 'run' command implementation

########### Imports #############
import os, sys
from  config import *
import utils

########### Globals #############
# Get the sub-command from the user
app_name = sys.argv[2]
plat = sys.argv[3]
arch = UK_DEF_ARCH

########### Functions ###########

if plat == 'kvm':
    plat_script = KVM_SCRIPT
elif plat == 'xen':
    plat_script = XEN_SCRIPT
elif plat == 'solo5':
    plat_script = SOLO5_SCRIPT
else:
    print('Invalid platform !')
    exit()
# Build the argument for platform script
args = ' -k '+UK_APPS_DIR+'/'+app_name+'/build/'+app_name+'_'+plat+'-'+arch
# Create the command to run the unikernel for given platform
cmd = plat_script+args
# Run the command
if not os.system(cmd):
    print('An error occured during execution!')




