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

import re

BRANCH_MASTER="master"
BRANCH_STAGING="staging"

UK_GITHUB_ORG='unikraft'

# Match against dereferenced tags only
# https://stackoverflow.com/a/15472310
GIT_TAG_PATTERN=re.compile(r'refs/tags/RELEASE-([\d\.]+)\^\{\}')
GIT_BRANCH_PATTERN=re.compile(r'refs/heads/(.*)')

GITHUB_ORIGIN="https://github.com"
UNIKRAFT_ORG="unikraft"
UNIKRAFT_CORE="%s/%s/%s" % (GITHUB_ORIGIN, UNIKRAFT_ORG, "unikraft.git")

REPO_VERSION_DELIMETERE = "@"
ORG_DELIMETERE = "/"

REPO_VALID_URL_PREFIXES = (
    'http://',
    'https://',
    'git://',
    'git@',
    'file:///'
)

SUPPORTED_FILENAMES = [
    'kraft.yaml',
    'kraft.yml',
]

UNIKERNEL_IMAGE_FORMAT="%s/build/%s_%s-%s"
UNIKERNEL_IMAGE_FORMAT_DGB="%s/build/%s_%s-%s.dbg"

DEPS_JSON="deps.json"
DOT_CONFIG=".config"
DEFCONFIG="defconfig"
MAKEFILE_UK="Makefile.uk"
ENV_VAR_PATTERN=re.compile(r'([A-Z_^=]+)=(\'[/\w\.\-\s]+\')')