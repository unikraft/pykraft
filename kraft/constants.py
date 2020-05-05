# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Europe Ltd., NEC Corporation. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
from __future__ import absolute_import
from __future__ import unicode_literals

import re

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

BRANCH_MASTER = "master"
BRANCH_STAGING = "staging"

UK_GITHUB_ORG = 'unikraft'

# Match against dereferenced tags only
# https://stackoverflow.com/a/15472310
GIT_UNIKRAFT_TAG_PATTERN = re.compile(r'refs/tags/RELEASE-([\d\.]+)\^\{\}')
GIT_TAG_PATTERN = re.compile(r'refs/tags/([\w\d\.-]+)[\^\{\}]?')
GIT_BRANCH_PATTERN = re.compile(r'refs/heads/(.*)')
SEMVER_PATTERN = re.compile(
    r"""
        (?P<major>0|[1-9]\d*)
        \.
        (?P<minor>0|[1-9]\d*)
        \.
        (?P<patch>0|[1-9]\d*)
        (?:-(?P<prerelease>
            (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
            (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
        ))?
        (?:\+(?P<build>
            [0-9a-zA-Z-]+
            (?:\.[0-9a-zA-Z-]+)*
        ))?
    """,
    re.VERBOSE,
)

GITHUB_ORIGIN = "https://github.com"
UNIKRAFT_ORG = "unikraft"
UNIKRAFT_CORE = "%s/%s/%s" % (GITHUB_ORIGIN, UNIKRAFT_ORG, "unikraft.git")
UNIKRAFT_ORIGIN = "%s/%s" % (GITHUB_ORIGIN, UNIKRAFT_ORG)

REPO_VERSION_DELIMETERE = "@"
ORG_DELIMETERE = "/"

REPO_VALID_URL_PREFIXES = (
    'http://',
    'https://',
    'git://',
    'git@',
    'file://'
)

SUPPORTED_FILENAMES = [
    'kraft.yaml',
    'kraft.yml',
]

TARBALL_SUPPORTED_EXTENSIONS = [
    '.zip',
    '.tar.gz',
    '.tar',
]

UNIKERNEL_IMAGE_FORMAT = "%s/build/%s_%s-%s"
UNIKERNEL_IMAGE_FORMAT_DGB = "%s/build/%s_%s-%s.dbg"

DOT_CONFIG = ".config"
DEFCONFIG = "defconfig"
MAKEFILE_UK = "Makefile.uk"
CONFIG_UK = "Config.uk"
ENV_VAR_PATTERN = re.compile(r'([A-Z_^=]+)=(\'[/\w\.\-\s]+\')')

UNIKRAFT_WORKDIR = ".unikraft"
UNIKRAFT_COREDIR = "unikraft"
UNIKRAFT_LIBSDIR = "libs"
UNIKRAFT_APPSDIR = "apps"

GITCONFIG_GLOBAL = "~/.gitconfig"
GITCONFIG_LOCAL = ".git/config"
URL_VERSION = '$VERSION'

KRAFTCONF = ".kraftrc"
KRAFTCONF_DELIMETER = "/"
KRAFTCONF_INIT_WORKDIR = "init/workdir"
KRAFTCONF_CONFIGURE_PLATFORM = "configure/platform"
KRAFTCONF_CONFIGURE_ARCHITECTURE = "configure/architecture"

KCONFIG = 'CONFIG_%s'
KCONFIG_Y = 'y'
KCONFIG_N = 'n'
KCONFIG_EQ = '%s=%s'
KCONFIG_ARCH_NAME = "CONFIG_ARCH_%s"
KCONFIG_PLAT_NAME = "CONFIG_PLAT_%s"
KCONFIG_LIB_NAME = "CONFIG_LIB%s"

UK_CORE_ARCH_DIR = '%s/arch'
UK_CORE_PLAT_DIR = '%s/plat'
UK_VERSION_VARNAME = '$(%s_VERSION)'

CONFIG_UK_ARCH = re.compile(
    r"""
        if\s+\(([\w\_]+)\)[\n\s]+source\s+"\$\(UK_BASE\)(\/arch\/[\w_]+\/(\w+)\/)Config\.uk"
    """,
    re.VERBOSE
)
CONFIG_UK_PLAT = re.compile(r'menuconfig\s+([\w\_]+)')
CONFIG_UK_LIB = re.compile(r'config\s+([\w\_]+)')

UK_GITHUB_NAMING_FORMAT = r'(%s)-([^.]+)'
UK_GITHUB_CORE_FORMAT = re.compile(r'(unikraft)/(unikraft)')

UK_COMPAT_CORE_v0_4_0 = "0.4.0"

KRAFT_SPEC_V04 = '0.4'
KRAFT_SPEC_LATEST = KRAFT_SPEC_V04

UK_DBG_EXT = '.dbg'
TMPL_EXT = '.tmpl'

TEMPLATE_CONFIG = 'cookiecutter.json'
TEMPLATE_MANIFEST = 'manifest.yaml'

QEMU_GUEST = 'qemu-guest'
XEN_GUEST = 'xen-guest'
