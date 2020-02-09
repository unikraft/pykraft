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

import os
import re
import sys

import functools
from enum import Enum
from datetime import datetime
from urllib.parse import urlparse

# from tqdm import tqdm

from git import Repo as GitRepo
from git import RemoteProgress
from git import InvalidGitRepositoryError
from git import NoSuchPathError
from git import GitCommandError
from git.cmd import Git as GitCmd
from git.exc import GitCommandError

from kraft.logger import logger

from kraft.component import Component
from kraft.kraft import kraft_context

from kraft.errors import InvalidRepositoryFormat
from kraft.errors import InvalidRepositorySource

from kraft.constants import BRANCH_MASTER
from kraft.constants import BRANCH_STAGING
from kraft.constants import GIT_TAG_PATTERN
from kraft.constants import GIT_BRANCH_PATTERN

class Repository(object):
    name = None
    component_type = None

    git = None
    source = None
    localdir = None

    version = None
    known_versions = {}
    version_head = None

    last_updated = None
    last_checked = None

    def __init__(self,
        name=None,
        source=None,
        version=None,
        localdir=None,
        component_type=None,
        force_update=False,
        download=False):
        """Determine whether the provided URL is a Git repository and then
        remotely retrieve the contents of said repository based on yjr
        particular url and branch.  Returns boolean for success state of
        initializing the Repo object."""

        if source is None or len(source) == 0:
            raise InvalidRepositorySource(source)

        version_head = None

        # In good scenarios, we have already been given key information about
        # this repository
        if component_type is None or name is None:
            # Let's passively determine the name and type first before we clone,
            # as this helps us determine where to place the repository when we
            # want to clone it.
            component_type, name = self.passively_determine_type_and_name(source)

        already_downloaded = False

        if len(self.known_versions) == 0 or force_update or download:
            self.known_versions = self.list_remote_references(source=source)

        # Determine how to set the version
        if version is not None:
            self.version = version
        elif BRANCH_MASTER in self.known_versions:
            self.version = BRANCH_MASTER
        elif BRANCH_STAGING in self.known_versions:
            self.version = BRANCH_STAGING
        else:
            raise NoSuchReferenceInRepo

        # If we cannot determine the type passively, we must clone the
        # repository into a temporary location and manually introspect
        # the files to determine its type.
        if component_type is None or name is None:
            component_type, name = self.intrusively_determine_type_and_name(source)

        # If we cannot determine the name and type passively we must
        # throw an error and prompt the user for more information to
        # address this roblem.
        if component_type is None or name is None:
            raise NoTypeAndNameRepo
        
        # Check if we already have a repository saved locally with this remote
        # url set.  If so, we do not need to make an outbound connection to
        # determine whether the repository is "real".
        if localdir is None:
            self.localdir = self.determine_localdir(component_type=component_type, name=name)
        else:
            self.localdir = localdir

        # Populate the repository information if we have made it this far, as it
        # means that the repository is valid and usable.
        self.name = name
        self.component_type = component_type
        self.source = source

        if download or force_update:
            self.update()
    
        logger.debug("Initialized %s!" % self.name)
        if not self.__get_cache(source):
            logger.debug("Saving %s into cache..."  % source)
            self.__set_cache(source, self)

    @classmethod
    @kraft_context
    def __get_cache(ctx, cls, source=None):
        """Determine if the Repository via its source has already been cached."""
        return ctx.cache.get(source)

    @classmethod
    @kraft_context
    def __set_cache(ctx, cls, source=None, repository=None):
        """Set the repository cache for this source."""
        ctx.cache.set(source, repository)

    def __new__(cls, *args, **kwargs):
        """Initialize the Repository from cache or from principal."""

        source = None

        if 'source' in kwargs:
            source = kwargs['source']
            existing = cls.__get_cache(source)

            if existing and isinstance(existing, Repository):
                logger.debug("Retrieving %s from cache..."  % source)
                return existing
        
        return super(Repository, cls).__new__(cls)
        
    @classmethod
    def from_source_string(cls, name=None, source=None, version=None, component_type=None, force_update=False):
        return cls(
            name=name,
            source=source,
            version=version,
            component_type=component_type,
            force_update=force_update,
        )

    def list_remote_references(self, source=None):
        """List references in a remote repository"""

        versions = {}

        if source is None:
            return versions

        g = GitCmd()

        logger.debug("Probing %s..." % source)

        try:
            remote = g.ls_remote(source) 
        except GitCommandError as e:
            logger.fatal("Could not connect to Github: %s" % str(e))
            sys.exit(1)

        for refs in g.ls_remote(source).split('\n'):
            hash_ref_list = refs.split('\t')

            # Empty repository
            if len(hash_ref_list) == 0:
                continue

            # Check if branch
            ref = GIT_BRANCH_PATTERN.search(hash_ref_list[1])
            if ref is not None:
                versions[ref.group(1)] = hash_ref_list[0]
                continue

            # Check if version tag
            ref = GIT_TAG_PATTERN.search(hash_ref_list[1])
            if ref is not None:
                versions[ref.group(1)] = hash_ref_list[0]

        self.last_checked = datetime.now()

        return versions

    def passively_determine_type_and_name(self, name):
        """Determine the name and type of the repository by checking the name of
        the repository against a well-known "type-name" syntax.  We can pass a
        name into this method, whether it's a URL, a directory or a name."""

        for component_type, member in Component.__members__.items():
            ref = member.search(name)

            if ref is not None:
                return member, ref.group(2)

        return None, None

    # TODO: Intrusively determine type and name from a remote URL by fetching
    # its contents.
    def intrusively_determine_type_and_name(self, source):
        """If no type can be specified, use an intrusive technique to determine
        the type of repository that is wanting to be made available.  This is
        acheived by inspecting the top-level directory of the repository's
        `Makefile.uk` which will, if correctly configured, include one of four
        possible Makefile functions:

            - addplat_s
            - addlib_s
            - addplatlib_s

        More on registration techniques can be found here:
        https://github.com/unikraft/unikraft/blob/staging/support/build/Makefile.rules#L124

        If none of these types can be determined, we will default to an an
        application."""

        return None, None

    def determine_localdir(self, component_type=None, name=None):
        """Sets the local directory for the repository based on the workspace
        setup which is detgermined by the environmental variables UK_WORKDIR,
        UK_ROOT, UK_LIBS or UK_APPS"""
        localdir = None

        if component_type is None or name is None:
            raise NoTypeAndNameRepo
            return False

        if component_type is Component.CORE:
            localdir = os.environ['UK_ROOT']

        elif component_type is Component.APP:
            localdir = os.path.join(os.environ['UK_APPS'], name)

        elif component_type is Component.LIB:
            localdir = os.path.join(os.environ['UK_LIBS'], name)

        # Platform is a special repository that is placed _within_ the core
        # unikraft repository for now.
        elif component_type is Component.PLAT:
            localdir = os.path.join(os.environ['UK_ROOT'], 'plat', name)

        return localdir

    def update(self):
        """Update this particular repository."""

        repo = None

        try:
            repo = GitRepo(self.localdir)
        
        # Not a repository? No problem, let's clone it:
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            repo = GitRepo.init(self.localdir)
            repo.create_remote('origin', self.source)

        try:
            for fetch_info in repo.remotes.origin.fetch():
                logger.debug("Updated %s %s to %s" % (self.source, fetch_info.ref, fetch_info.commit))
            self.last_checked = datetime.now()
        except GitCommandError as e:
            logger.error("Could not fetch %s: %s" % (self.source, str(e)))
        
        # self.checkout(self.version)
        # self.last_updated = datetime.fromtimestamp(repo.head.commit.committed_date)

    def checkout(self, version=None, retry=False):
        """Checkout a version of the repository."""

        if version is None:
            version = self.version

        if version is not None:

            try:
                repo = GitRepo(self.localdir)
            
            except (NoSuchPathError, InvalidGitRepositoryError):
                logger.debug("Attempting to checkout %s before update!" % self)

                # Allow one retry
                if retry is False:
                    self.update()
                    self.checkout(version, True)
                    return
        
            try:
                # If this throws an exception, it means we have never checked
                # out the repository before.
                commit_hash = str(repo.head.commit)
                
                if commit_hash.startswith(version) \
                or version in self.known_versions and self.known_versions[version] == commit_hash:
                    logger.debug("%s already at %s..." % (self.name, version))         
                else:
                    logger.debug("Checking-out %s@%s..." % (self.name, version))
            except ValueError as e:
                pass

            try:           
                repo.git.checkout(version)
            except GitCommandError as e:
                logger.error("Could not checkout %s@%s: %s" % (self.name, version, str(e)))
                sys.exit(1)

    @property
    def shortname(self):
        return '%s/%s' % (self.component_type.shortname, self.name)

    @property
    def longname(self):
        return '%s@%s' % (self.name, self.version)

    @property
    def latest_release(self):
        """Attempt retrieving the latest version number of a repository by 
        removing the staging and master branches.  If no version number is
        available, return 'master' since this is usually the latest stable
        version."""
        versions = list(self.known_versions.keys())

        if BRANCH_MASTER in versions:
            versions.remove(BRANCH_MASTER)
        if BRANCH_STAGING in versions:
            versions.remove(BRANCH_STAGING)
        
        if len(versions) > 0:
            return versions[-1]
        
        if BRANCH_MASTER in self.known_versions:
            return BRANCH_MASTER
        if BRANCH_STAGING in self.known_versions:
            return BRANCH_STAGING
        
        return self.version
    
    @property
    def type(self):
        return self.component_type

    @property
    def is_downloaded(self):
        try:
            GitRepo(self.localdir)
            return True
        except InvalidGitRepositoryError:
            return False

    def __repr__(self):
        """Python representation"""
        return '<Repo %r>' % self.source

    def __str__(self):
        """String representation"""
        return self.longname

class RepositoryConfig(object):
    _name = None
    _repository = None
    _config = None

    def __init__(self, name, repository, config):
        self._name = name or None
        self._repository = repository or None
        self._config = config or {}
    
    @property
    def name(self):
        return self._name
    
    @property
    def repository(self):
        return self._repository
    
    @property
    def config(self):
        return self._config

class RepositoryManager(object):
    _repositories = []

    def __init__(self, repository_base=[]):
        self._repositories = repository_base or []

    def add(self, name, repository, config):
        self._repositories.append(RepositoryConfig(name, repository, config))

    def get(self, key, default=None):
        for repository in self._repositories:
            if getattr(repository, key) == value:
                return repository

    def all(self):
        return self._repositories

    def checkout(self):
        for repo in self.all():
            repo.repository.checkout()

    def update(self):
        for repo in self.all():
            repo.repository.update()
