# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Europe Laboratories GmbH., NEC Corporation.
#                     All rights reserved.
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

from .git import git_probe_remote_versions
from .git import GitLibraryProvider
from kraft.const import GITHUB_ORIGIN
from kraft.const import REPO_VALID_URL_PREFIXES
from kraft.const import TARBALL_SUPPORTED_EXTENSIONS
# from git.cmd import Git as GitCmd


def github_org_name(source=None):
    for prefix in REPO_VALID_URL_PREFIXES:
        if source.startswith(prefix):
            source = source[len(prefix):]

    github_parts = source.split('/')

    return github_parts[1], github_parts[2]


class GitHubLibraryProvider(GitLibraryProvider):

    @classmethod
    def is_type(cls, origin=None):
        if origin is None:
            return False

        if GITHUB_ORIGIN in origin:
            return True

        return False

    def probe_remote_versions(self, source=None):
        if source is None:
            source = self._source

        # Convert a archive URL to a git URL
        if source.endswith(tuple(TARBALL_SUPPORTED_EXTENSIONS)):
            org, repo = github_org_name(source)

            self._source = source = "https://%s/%s/%s.git" % (
                GITHUB_ORIGIN, org, repo
            )

        return git_probe_remote_versions(source)

    def version_source_archive(self, varname=None):
        if varname is None:
            return self.source

        source = self.source

        org, repo = github_org_name(source)

        if repo.endswith('.git'):
            repo = repo[:-4]

        return "https://github.com/%s/%s/archive/%s.zip" % (org, repo, varname)
