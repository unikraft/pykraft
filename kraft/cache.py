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
#
# THIS HEADER MAY NOT BE EXTRACTED OR MODIFIED IN ANY WAY.

import os
import re
import click
from github import Github
from .logger import logger
from kraft import __program__
from datetime import datetime
from fcache.cache import FileCache
from .component import KraftComponent
from .repo import Repo, InvalidRepo, NoSuchReferenceInRepo, NoTypeAndNameRepo, MismatchVersionRepo

UK_GITHUB_ORG='unikraft'
UK_CORE_ARCH_DIR='%s/arch'
UK_CORE_PLAT_DIR='%s/plat'
UK_CONFIG_FILE='%s/Config.uk'
# CONFIG_UK_ARCH=re.compile(r'^CONFIG_UK_ARCH := ([\w]+)$')
CONFIG_UK_ARCH=re.compile(r'source "\$\(UK_BASE\)(\/arch\/[\w_]+\/(\w+)\/)Config\.uk"$')
STALE_TIMEOUT=604800 # 7 days

class Cache(object):
    cachedir = None
    caches = {}

    def __init__(self):
        self.cachedir = os.path.join(os.environ['UK_WORKDIR'], 'kraft.cache')

        if os.path.isdir is False:
            try:
                os.mkdir(self.cachedir)
            except OSError as e:
                log.error("Could not create kraft cache directory: %s: %s" % (self.cachedir, str(e)))

        if 'UK_KRAFT_GITHUB_TOKEN' in os.environ:
            self.github = Github(os.environ['UK_KRAFT_GITHUB_TOKEN'])
        else:
            self.github = Github()

        # Populate varying caches
        for type, member in KraftComponent.__members__.items():
            if member.shortname not in self.caches:
                self.caches[member.shortname] = FileCache(
                    app_cache_dir = self.cachedir,
                    appname = __program__ + '.' + member.shortname,
                    flag='cs'
                )

    def is_stale(self):
        """Determine if the list of remote repositories is stale.  Return a
        boolean value if at least one repository is marked as stale."""

        logger.debug("Checking cache for staleness...")

        biggest_timeout = 0
        repos = self.repos()

        # If there is nothing cached, this is also stale
        if len(repos) == 0:
            return True

        for repo in repos:
            # If we have never checked, this is stale
            if repos[repo].last_checked is None:
                return True

            diff = (datetime.now() - repos[repo].last_checked).total_seconds()
            if diff > biggest_timeout:
                biggest_timeout = diff

        if biggest_timeout > STALE_TIMEOUT:
            return True

        return False

    def update(self, use_branch=None):
        """Update the list of remote repositories."""

        logger.info("Populating lists from Github...")

        self.flush()

        org = self.github.get_organization(UK_GITHUB_ORG)

        for repo in org.get_repos():
            # There is one repository which contains the codebase to kraft
            # itself (this code!) that is returned in this iteration.  Let's
            # filter it out here so we don't receive a prompt for an invalid
            # repository.
            if repo.git_url == 'git://github.com/unikraft/tools.git':
                continue

            if use_branch is None:
                branch = repo.default_branch
            else:
                branch = use_branch

            try:
                self.add_repo(Repo(
                    remoteurl=repo.git_url,
                    branch=branch,
                    force_update=True,
                    download=True
                ))
            except (InvalidRepo, NoSuchReferenceInRepo, NoTypeAndNameRepo, MismatchVersionRepo) as e:
                logger.error("Could not add repository: %s: %s" % (repo.git_url, str(e)))


        # FIXME:  This is a niave architecture-platform determination which
        # simply scans the unikraft/unikraft directory for relevant files and
        # directories.  Whilst this is how it unikraft determines this supported
        # components in reality, it uses KConfig to perform verification.
        for core in self.caches[KraftComponent.CORE.shortname]:
            repo = self.caches[KraftComponent.CORE.shortname][core]

            # Test for additional architectures which reside inside the core
            # unikraft repo
            with open(UK_CONFIG_FILE % (UK_CORE_ARCH_DIR % repo.localdir)) as f:
                for line in f:
                    match = CONFIG_UK_ARCH.findall(line)
                    if len(match) > 0:
                        path, arch = match[0]

                        try:
                            self.add_repo(Repo(
                                name=arch,
                                download=False,
                                force_update=False,
                                branch=repo.git_branch,
                                type=KraftComponent.ARCH,
                                remoteurl=repo.remoteurl,
                                tag=repo.current_version,
                                version=repo.current_version,
                                localdir=os.path.join(repo.localdir, path)))
                        except (InvalidRepo, NoSuchReferenceInRepo, NoTypeAndNameRepo, MismatchVersionRepo) as e:
                            logger.error("Could not add repository: %s: %s" % (os.path.join(repo.localdir, path), repo.longname))

            # Test for additional platforms which reside inside the core
            # unikraft repo
            for dir in os.scandir(UK_CORE_PLAT_DIR % repo.localdir):
                if os.path.exists(UK_CONFIG_FILE % dir.path):
                    try:
                        self.add_repo(Repo(
                            name=dir.name,
                            download=False,
                            localdir=dir.path,
                            force_update=False,
                            branch=repo.git_branch,
                            remoteurl=repo.remoteurl,
                            tag=repo.current_version,
                            type=KraftComponent.PLAT,
                            version=repo.current_version))
                    except (InvalidRepo, NoSuchReferenceInRepo, NoTypeAndNameRepo, MismatchVersionRepo) as e:
                        logger.error("Could not add repository: %s: %s" % (dir.name, repo.longname))

    def flush(self):
        """Destroy local cache."""

        for key, val in self.caches.items():
            if val is None:
                self.caches[key].delete()

    def repos(self, type=None):
        """Return a complete list of repositories in a single dictionary."""

        repos = {}

        # Return a list of all repositories
        if type is None:
            for type, member in KraftComponent.__members__.items():
                for repo in self.caches[member.shortname]:
                    repos[repo] = self.caches[member.shortname][repo]

        # Return the specific type
        elif isinstance(type, KraftComponent):
            return self.caches[type.shortname]

        return repos

    def repos_names(self, type=None):
        """Return a complete list of repositories in a single array of only
        their names"""
        repos = []

        # Return a list of all repositories
        if type is None:
            for type, member in KraftComponent.__members__.items():
                for repo in self.caches[member.shortname]:
                    repos.append(self.caches[type.shortname][repo].name)

        # Return the specific type
        elif isinstance(type, KraftComponent):
            for repo in self.caches[type.shortname]:
                repos.append(self.caches[type.shortname][repo].name)

        return repos

    # Add a new repository to the cache
    def add_repo(self, repo):
        if isinstance(repo, Repo):
            self.caches[repo.type.shortname][repo.name] = repo
            self.caches[repo.type.shortname].sync()
        else:
            logger.error("Repository was not initialized correctly and cannot be added!")
