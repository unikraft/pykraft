#!/usr/bin/env python3
# Core 'kraft' script implementation.

# System imports
import argparse
import sys
import os

# Custom imports
import srcs.kraft.modules.config
import srcs.kraft.modules.utils

class Kraft(object):

    # Initialize Kraft command line system.
    def __init__(self):
        parser = argparse.ArgumentParser(
        description='A command line tool to do "Unikraft"',
        usage='''kraft <command> [<args>]

Available kraft <command> are:
   list         :Lists all available app repos and internal/extermal plats on unikraft github
   fetch        :Clones the chosen app repo and its dependencies, and set the right branches/commits.
   configure    :Uses the default .config file in the app repo and Unikraft's build system's
                 make defconfig to set up a .config file to build from
   build        :Essentially runs make. If kraft fetch and kraft configure haven't been run, kraft build
                 runs these first. If the arch's not given, uses the local host's CPU arch
   createfs     :Generates filesystems for multiple libs and apps.
   run          :Runs the unikraft generated unikernels on multiple platforms
                 (Requires kvm-guest, xen-guest and solo5-hvt installed)
   update       :git pull's from all cloned repos. If git-tag is given, checkout that tag and pull.
   create       :Creates the repo skeleton which can be directly pushed on to Github
''')
        parser.add_argument('cmd', help='Command to run')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.cmd):
            print('Unrecognized command')
            print(parser.usage)
            exit(1)
        # Dispatcher to invoke method with kraft 'sub-command' names
        getattr(self, args.cmd)()


#####################   Command implementations  #######################
    # 'list' command handler
    def list(self):
        #print('Process "list" command...'+ self.script_name +"\n")
        parser = argparse.ArgumentParser(
        description='Lists all the available unikraft "application" and "platform" repositories.',
        usage='''kraft list <sub-command>

Available kraft list <sub-command> are:
   apps     :Lists all available 'application' repos on unikraft github
   plats    :Lists all available 'platform' repos on unikraft github
   ''')
        # Add sub commands supported by the "list" command
        parser.add_argument('sub_cmd', choices=['apps', 'plats'], help='Lists available repositories of given type (apps | plats) ')
        args = parser.parse_args(sys.argv[2:])
        # Invoke another script which has the actual implementation of 'list' command
        utils.invoke_sub_cmd(sys.argv[1], args.sub_cmd)

    # 'fetch' command handler
    def fetch(self):
        print("Fetching unikraft source code...")
        parser = argparse.ArgumentParser(
        description='Clones the given app repository, all of its dependencies, creates proper directory structure',
        usage='''kraft fetch <sub-command>

Available kraft <sub-command> are:
   <app>     :Application name
   <plats>   :Target platform
   ''')
        # Add sub commands supported by the "fetch" command
        parser.add_argument('sub_cmd', help='Lists available repositories of given type (apps | plats) ')
        args = parser.parse_args(sys.argv[2:])
        # Invoke another script which has the actual implementation of 'list' command
        utils.invoke_sub_cmd(sys.argv[1], args.sub_cmd)

    # 'configure' command handler
    def configure(self):
        print("Configuring unikraft build...")

    # 'configure' command handler
    def build(self):
        print("Building unikernel...")

    # 'configure' command handler
    def update(self):
        print("Updating unikarft source code...")

    # 'configure' command handler
    def create(self):
        print("Creating repo skeleton...")




if __name__ == '__main__':
    Kraft()

