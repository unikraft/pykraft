#!/usr/bin/python3.7

# Global configs
BASE_URL = 'https://github.com/'
BASE_API_URL='https://api.github.com/'
USER_NAME='unikraft'
UK_URL=BASE_API_URL + 'users/'+ USER_NAME + '/repos'
APPS_REPO_PREFIX='app-'
PLATS_REPO_PREFIX='plat-'
LIBS_REPO_PREFIX= 'lib-'
CMD_DIR='srcs/kraft/commands'
UK_DEPS_BASE_URL = 'https://raw.githubusercontent.com/'
UK_DEPS_URL = UK_DEPS_BASE_URL + USER_NAME

CORE_REPO_URL = BASE_URL+USER_NAME+'/'
APPS_REPO_URL = BASE_URL+USER_NAME+'/'+APPS_REPO_PREFIX
LIBS_REPO_URL = BASE_URL+USER_NAME+'/'+LIBS_REPO_PREFIX
PLATS_REPO_URL = BASE_URL+USER_NAME+'/'+PLATS_REPO_PREFIX
DEPS_JSON_FILE = 'deps.json'
TO_BLACK_HOLE = '> /dev/null 2>&1'
UK_PY_FS = 'minrootfs.tgz'
#Standard commands
GIT = 'git'
PULL = GIT+' pull'
CLONE = GIT+' clone'
UK_DEF_ARCH = 'x86_64'

# Unikraft Source Code Directory Structure
UK_BASE_SRC='uk_src'
UK_CORE_DIR='unikraft'
UK_APPS_DIR='apps'
UK_LIBS_DIR='libs'
UK_PLATS_DIR='plats'

#Platform scripts
KVM_SCRIPT='kvm-guest'
XEN_SCRIPT='xen-guest'
SOLO5_SCRIPT='solo5-guest'

# Main Command Strings
KRAFT_CMD_LIST='list'
KRAFT_CMD_FETCH='fetch'
KRAFT_CMD_CONFIGURE='configure'
KRAFT_CMD_BUID='build'
KRAFT_CMD_CREATEFS='createfs'
KRAFT_CMD_RUN='run'
KRAFT_CMD_UPDATE='update'
KRAFT_CMD_CREATE='create'

# Sub Command Strings
KRAFT_SUBCMD_APPS='apps'
KRAFT_SUBCMD_PLATS='plats'
KRAFT_SUBCMD_APPREPO='apprepo'
KRAFT_SUBCMD_LIBREPO='librepo'


