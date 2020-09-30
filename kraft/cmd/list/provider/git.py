# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Laboratories Europe GmbH., NEC Corporation.
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
# flake8: noqa
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import sys
import uuid

from git import RemoteProgress
from git import Repo as GitRepo
from git import InvalidGitRepositoryError
from git import GitCommandError
from git import NoSuchPathError
from atpbar import find_reporter

from kraft.logger import logger
from kraft.const import GIT_UNIKRAFT_TAG_RELEASE

from .provider import ListProvider


class GitProgressBar(RemoteProgress):
    def __init__(self, max_lines=10, label=None):
        RemoteProgress.__init__(self)
        self.taskid = uuid.uuid4()
        self.reporter = find_reporter()
        self.pid = os.getpid()
        self.label = label

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.reporter.report(dict(
            taskid=self.taskid,
            name=self.label,
            done=int(cur_count),
            total=int(max_count),
            pid=self.pid,
            in_main_thread=True
        ))


class GitListProvider(ListProvider):
    @classmethod
    def download(cls, manifest=None, localdir=None, version=None,
            override_existing=False):
        
        try:
            repo = GitRepo(localdir)

        except (InvalidGitRepositoryError, NoSuchPathError):
            repo = GitRepo.init(localdir)
        
        if manifest.git is not None:
            try:
                repo.create_remote('origin', manifest.git)
            except GitCommandError as e:
                pass

        try:
            if sys.stdout.isatty():
                repo.remotes.origin.fetch(
                    progress=GitProgressBar(
                        label="%s@%s" % (str(manifest), version.version)
                    )
                )
            else:
                for fetch_info in repo.remotes.origin.fetch():
                    logger.debug("Updated %s %s to %s" % (
                        manifest.git,
                        fetch_info.ref,
                        fetch_info.commit
                    ))

            # self.last_checked = datetime.now()
        except (GitCommandError, AttributeError) as e:
            logger.error("Could not fetch %s: %s" % (manifest.git, str(e)))

        if version.git_sha is not None:
            repo.git.checkout(version.git_sha)
