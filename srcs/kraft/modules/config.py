#!/usr/bin/python3.7

# Global configs
BASE_URL='https://api.github.com/'
USER_NAME='unikraft'
UK_URL=BASE_URL + 'users/'+ USER_NAME + '/repos'
APPS_REPO_PREFIX='app-'
PLATS_REPO_PREFIX='plat-'
CMD_DIR='srcs/kraft/commands'

# Unikraft Source Code Directory Structure
UK_BASE_SRC='uk_src'
UK_CORE_DIR='unikraft'
UK_APPS_DIR='apps'
UK_LIBS_DIR='libs'
UK_PLATS_DIR='plats'

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




