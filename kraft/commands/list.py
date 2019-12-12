#!/usr/bin/env python3
# Kraft 'list' command implementation

########### Imports #############
import sys
import requests
import json
from config import *

########### Globals #############

# Place holder for repo-name 'prefixe'
repo_prefix = ""
repo_found = False
# Get the sub-command from the user
sub_cmd = sys.argv[1]

########### Functions ###########
# Upudates the repo prefix according to the command supplied by the user.
def get_repo_prefix():
    global repo_prefix
    if sub_cmd == KRAFT_SUBCMD_APPS:
        repo_prefix = APPS_REPO_PREFIX
    else:
        repo_prefix = PLATS_REPO_PREFIX

# Prints the available repository list
def get_repo_list():
    global repo_found
    request = requests.get(UK_URL)
    json = request.json()
    for i in range(0,len(json)):
        if repo_prefix not in json[i]['name']:
            continue
        if repo_found == False:
            print("Following repos are available - \n")
            repo_found = True

        print("Repo Name:",json[i]['name'].replace(repo_prefix,''))
        print("Repo URL:",json[i]['svn_url'])
        print("Repo Description:",json[i]['description'],"\n")

# Main routine
get_repo_prefix()
get_repo_list()
if repo_found == False:
    print("No repo available!")


