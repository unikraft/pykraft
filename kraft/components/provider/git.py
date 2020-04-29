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

from git import Repo as GitRepo
from git.cmd import Git as GitCmd
from git import GitCommandError

from .provider import Provider

from kraft.logger import logger

from kraft.constants import UNIKRAFT_ORIGIN
from kraft.constants import GIT_TAG_PATTERN
from kraft.constants import GIT_BRANCH_PATTERN
from kraft.constants import GIT_UNIKRAFT_TAG_PATTERN

def git_probe_remote_versions(source=None):
    """List references in a remote repository"""

    versions = {}

    if source is None:
        return versions
    
    if source.startswith("file://"):
        source = source[7:]

    g = GitCmd()

    logger.debug("Probing remote git repository: %s..." % source)

    try:
        remote = g.ls_remote(source)
    
    except GitCommandError as e:
        logger.fatal("Could not connect to repository: %s" % str(e))
        return versions

    for refs in g.ls_remote(source).split('\n'):
        hash_ref_list = refs.split('\t')

        # Empty repository
        if len(hash_ref_list) == 0 or hash_ref_list[0] == '':
            continue

        # Check if branch
        ref = GIT_BRANCH_PATTERN.search(hash_ref_list[1])

        if ref:
            versions[ref.group(1)] = hash_ref_list[0]
            continue

        # Check if version tag
        if source.startswith(UNIKRAFT_ORIGIN):
            ref = GIT_UNIKRAFT_TAG_PATTERN.search(hash_ref_list[1])
        
        else:
            ref = GIT_TAG_PATTERN.search(hash_ref_list[1])

        if ref:
            versions[ref.group(1)] = hash_ref_list[0]

    return versions

class GitProvider(Provider):

    @classmethod
    def is_type(cls, source=None):
        if source is None:
            return False
        
        try:
            if source.startswith("file://"):
                source = source[7:]
            
            GitRepo(source, search_parent_directories=True)
            return True
        
        except Exception as e:
            pass
        
        try:
            GitCmd().ls_remote(source)
            return True
        
        except Exception as e:
            pass
        
        return False
    
    def probe_remote_versions(self, source=None):
        if source is None:
            source = self.source
        
        return git_probe_remote_versions(source)
    
    def version_source_url(self, varname=None):
        return self.source

