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
import click

from datetime import datetime
from queue import Queue
from git.cmd import Git
from git import RemoteProgress
from git import Repo as GitRepo
from git import InvalidGitRepositoryError
from git import GitCommandError
from git import NoSuchPathError
from atpbar import find_reporter
from urllib.parse import urlparse

from kraft.types import break_component_naming_format
from kraft.util import ErrorPropagatingThread
from kraft.logger import logger
from kraft.const import GIT_UNIKRAFT_TAG_RELEASE
from kraft.const import UNIKRAFT_RELEASE_STABLE
from kraft.const import UNIKRAFT_RELEASE_STABLE_VARIATIONS
from kraft.const import UNIKRAFT_RELEASE_STAGING
from kraft.const import GIT_UNIKRAFT_TAG_PATTERN

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
    def is_type(cls, origin=None):
        if origin is None:
            return False

        g = Git()

        try:
            g.ls_remote(origin)
        except GitCommandError:
            return False
        
        return True

    @click.pass_context
    def probe(ctx, self, origin=None, items=None, return_threads=False):
        # TODO: There should be a work around to fix this import loop cycle
        from kraft.manifest import Manifest

        if self.is_type(origin) is False:
            return []
            
        threads = list()
        if items is None:
            items = Queue()
        
        manifest = ctx.obj.cache.get(origin)
        
        if manifest is None:
            manifest = Manifest(
                manifest=origin
            )

        if return_threads:
            thread = ErrorPropagatingThread(
                target=lambda *arg: items.put(get_component_from_git_repo(*arg)),
                args=(
                    ctx,
                    origin
                )
            )
            threads.append(thread)
            thread.start()
        else:
            items.put(get_component_from_git_repo(ctx, origin))
        
        return items, threads

    @classmethod
    def download(cls, manifest=None, localdir=None, version=None,
            override_existing=False, **kwargs):
        
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


def get_component_from_git_repo(ctx, origin=None):
    if origin is None:
        raise ValueError("expected origin")

    # TODO: There should be a work around to fix this import loop cycle
    from kraft.manifest import ManifestItem
    from kraft.manifest import ManifestItemVersion
    from kraft.manifest import ManifestItemDistribution
    from .types import ListProviderType
    
    # This is a best-effort guess at the type and name of the git repository
    # using the path to determine if it's namespaced.
    uri = urlparse(origin)
    pathparts = uri.path.split('/')
    if len(pathparts) >= 2:
        potential_typename = '/'.join(pathparts[-2:])
        _type, _name, _, _ = break_component_naming_format(potential_typename)
    elif len(pathparts) == 1:
        _type, _name, _, _ = break_component_naming_format(uri.path)

    if _type is None:
        raise ValueError("".join([    
            "Cannot determine the type of the repository: %s\n\n",
            "Please ensure it is of the naming convention <type>-<name> or ",
            "that it is namespaced in a directory <type>/<name>."
            ]) % origin
        )

    localdir = None
    if os.path.exists(origin):
        localdir = origin

    repo = GitRepo(origin)
    item = ManifestItem(
        provider=ListProviderType.GIT, 
        name=_name,
        type=_type.shortname,
        dist=UNIKRAFT_RELEASE_STABLE,
        git=origin,
        manifest=origin,
        localdir=localdir
    )

    stable = ManifestItemDistribution(
        name=UNIKRAFT_RELEASE_STABLE
    )

    staging = ManifestItemDistribution(
        name=UNIKRAFT_RELEASE_STAGING
    )

    for version in repo.tags:
        commit = repo.commit(version)
        
        # interpret the tag name for symbolic distributions
        ref = GIT_UNIKRAFT_TAG_PATTERN.match(str(version))
        if ref is not None:
            version = ref.group(1)

        stable.add_version(ManifestItemVersion(
            git_sha=str(commit),
            version=version,
            timestamp=datetime.fromtimestamp(int(commit.committed_date))
        ))

    item.add_distribution(stable)

    for ref in repo.git.branch('-r').split('\n'):
        # skip fast forwards
        if "->" in ref:
            continue

        branch = ref.strip().replace("origin/", "")
        if branch in UNIKRAFT_RELEASE_STABLE_VARIATIONS:
            continue # we've done this one seperately

        # Add this commit to the staging branch (this usually happens when
        # commits have been applied on top of a HEAD)
        if ref.strip() == "":
            dist = staging

        # Add the branch as a distribution
        else:
            dist = ManifestItemDistribution(
                name=branch,
            )

        # Add the latest commit to that branch as the only version
        commit = repo.commit(ref.strip())
        dist.add_version(ManifestItemVersion(
            git_sha=str(commit),
            version=str(commit)[:7],
            timestamp=datetime.fromtimestamp(int(commit.committed_date))
        ))

        item.add_distribution(dist)

    return item
