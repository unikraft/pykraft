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
import kconfiglib

from enum import Enum
from datetime import datetime
from urllib.parse import urlparse

from git import Repo as GitRepo
from git import RemoteProgress
from git import InvalidGitRepositoryError
from git import NoSuchPathError
from git import GitCommandError
from git.cmd import Git as GitCmd
from git.exc import GitCommandError

from kraft.logger import logger

from kraft.types import RepositoryType
from kraft.kraft import kraft_context

from kraft.errors import NoTypeAndNameRepo
from kraft.errors import InvalidRepositoryFormat
from kraft.errors import InvalidRepositorySource
from kraft.errors import NoSuchReferenceInRepo

from kraft.constants import KCONFIG
from kraft.constants import KCONFIG_Y
from kraft.constants import KCONFIG_EQ
from kraft.constants import BRANCH_MASTER
from kraft.constants import CONFIG_UK_LIB
from kraft.constants import UNIKRAFT_CORE
from kraft.constants import UK_CONFIG_FILE
from kraft.constants import CONFIG_UK_PLAT
from kraft.constants import BRANCH_STAGING
from kraft.constants import GIT_TAG_PATTERN
from kraft.constants import GIT_BRANCH_PATTERN

class Repository(object):
    _name = None
    _type = None

    _git = None
    _source = None
    _localdir = None

    _version = None
    _known_versions = {}
    _version_head = None

    _last_updated = None
    _last_checked = None

    _kconfig_extra = {}

    def __init__(self,
        name=None,
        source=None,
        version=None,
        localdir=None,
        repository_type=None,
        force_update=False,
        download=False,
        kconfig_extra={}):
        """Determine whether the provided URL is a Git repository and then
        remotely retrieve the contents of said repository based on yjr
        particular url and branch.  Returns boolean for success state of
        initializing the Repo object."""
        
        if source is None or len(source) == 0:
            raise InvalidRepositorySource(source)

        version_head = None

        # In good scenarios, we have already been given key information about
        # this repository
        if repository_type is None or name is None:
            # Let's passively determine the name and type first before we clone,
            # as this helps us determine where to place the repository when we
            # want to clone it.
            repository_type, name = self.passively_determine_type_and_name(source)

        already_downloaded = False

        if len(self._known_versions) == 0 or force_update or download:
            self.update_known_versions(source=source)
        
        # Determine how to set the version
        if version is not None:
            self._version = version
        elif BRANCH_MASTER in self._known_versions:
            self._version = BRANCH_MASTER
        elif BRANCH_STAGING in self._known_versions:
            self._version = BRANCH_STAGING
        else:
            raise NoSuchReferenceInRepo

        # If we cannot determine the type passively, we must clone the
        # repository into a temporary location and manually introspect
        # the files to determine its type.
        if repository_type is None or name is None:
            repository_type, name = self.intrusively_determine_type_and_name(source)

        # If we cannot determine the name and type passively we must
        # throw an error and prompt the user for more information to
        # address this roblem.
        if repository_type is None or name is None:
            raise NoTypeAndNameRepo
        
        # Check if we already have a repository saved locally with this remote
        # url set.  If so, we do not need to make an outbound connection to
        # determine whether the repository is "real".
        if localdir is None:
            self._localdir = self.determine_localdir(repository_type=repository_type, name=name)
        else:
            self._localdir = localdir

        # Populate the repository information if we have made it this far, as it
        # means that the repository is valid and usable.
        self._name = name
        self._type = repository_type
        self._source = source
        self._kconfig_extra = kconfig_extra

        if download or force_update:
            self.update()
        
        if self._type == RepositoryType.ARCH:
            return
        elif self._type == RepositoryType.PLAT and self._source == UNIKRAFT_CORE:
            return
        
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

        if 'repository_type' not in kwargs:
            return super(Repository, cls).__new__(cls)
        elif kwargs['repository_type'] == RepositoryType.ARCH:
            return super(Repository, cls).__new__(cls)
        elif kwargs['repository_type'] == RepositoryType.PLAT and kwargs['source'] == UNIKRAFT_CORE:
            return super(Repository, cls).__new__(cls)
        
        source = kwargs['source']
        existing = cls.__get_cache(source)

        if existing and isinstance(existing, Repository):
            return existing
        else:
            return super(Repository, cls).__new__(cls)

    @classmethod
    def from_source_string(cls, name=None, source=None, version=None, repository_type=None, force_update=False):
        return cls(
            name=name,
            source=source,
            version=version,
            repository_type=repository_type,
            force_update=force_update,
        )

    def update_known_versions(self, source=None):
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
            if len(hash_ref_list) == 0 or hash_ref_list[0] == '':
                continue

            # Check if branch
            ref = GIT_BRANCH_PATTERN.search(hash_ref_list[1])
            if ref:
                versions[ref.group(1)] = hash_ref_list[0]
                continue

            # Check if version tag
            ref = GIT_TAG_PATTERN.search(hash_ref_list[1])
            if ref:
                versions[ref.group(1)] = hash_ref_list[0]

        self._known_versions = versions
        self._last_checked = datetime.now()

    def passively_determine_type_and_name(self, name):
        """Determine the name and type of the repository by checking the name of
        the repository against a well-known "type-name" syntax.  We can pass a
        name into this method, whether it's a URL, a directory or a name."""

        for repository_type, member in RepositoryType.__members__.items():
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

    def determine_localdir(self, repository_type=None, name=None):
        """Sets the local directory for the repository based on the workspace
        setup which is detgermined by the environmental variables UK_WORKDIR,
        UK_ROOT, UK_LIBS or UK_APPS"""
        localdir = None

        if repository_type is None or name is None:
            raise NoTypeAndNameRepo
            return False

        if repository_type is RepositoryType.CORE:
            localdir = os.environ['UK_ROOT']

        elif repository_type is RepositoryType.APP:
            localdir = os.path.join(os.environ['UK_APPS'], name)

        elif repository_type is RepositoryType.LIB:
            localdir = os.path.join(os.environ['UK_LIBS'], name)

        # Platform is a special repository that is placed _within_ the core
        # unikraft repository for now.
        elif repository_type is RepositoryType.PLAT:
            localdir = os.path.join(os.environ['UK_ROOT'], 'plat', name)

        return localdir

    def update(self):
        """Update this particular repository."""

        repo = None

        try:
            repo = GitRepo(self._localdir)
        
        # Not a repository? No problem, let's clone it:
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            repo = GitRepo.init(self._localdir)
            repo.create_remote('origin', self._source)

        try:
            for fetch_info in repo.remotes.origin.fetch():
                logger.debug("Updated %s %s to %s" % (self._source, fetch_info.ref, fetch_info.commit))
            self._last_checked = datetime.now()
        except (GitCommandError, AttributeError) as e:
            logger.error("Could not fetch %s: %s" % (self._source, str(e)))
        
        # self.checkout(self._version)
        # self._last_updated = datetime.fromtimestamp(repo.head.commit.committed_date)

    @kraft_context
    def checkout(ctx, self, version=None, retry=False):
        """Checkout a version of the repository."""

        if ctx.dont_checkout:
            return

        if version is None:
            version = self.version

        if self._type == RepositoryType.ARCH:
            return
        elif self._type == RepositoryType.PLAT and self._source == UNIKRAFT_CORE:
            return
        elif version is not None:
            try:
                repo = GitRepo(self._localdir)
            
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
                
                # Determine if the repository has already been checked out at
                # this version
                if commit_hash.startswith(version) \
                or version in self._known_versions.keys() and self._known_versions[version] == commit_hash:
                    logger.debug("%s already at %s" % (self._name, version))
                    return
            except ValueError as e:
                pass

            logger.debug("Checking-out %s@%s..." % (self._name, version))

            # First simply attempting what was specified
            try:
                repo.git.checkout(version)
            except GitCommandError as e1:
                #  Don't try well-known branches with well-known RELEASE prefix:
                if version != BRANCH_MASTER and version != BRANCH_STAGING:
                    try:
                        repo.git.checkout('RELEASE-%s' % version)
                    except GitCommandError as e2:
                        if not ctx.ignore_checkout_errors:
                            logger.error("Could not checkout %s@%s: %s" % (self._name, version, str(e2)))
                            sys.exit(1)
                elif not ctx.ignore_checkout_errors:
                    logger.error("Could not checkout %s@%s: %s" % (self._name, version, str(e1)))
                    sys.exit(1)

    @property
    def name(self):
        return self._name
    
    @property
    def shortname(self):
        return '%s/%s' % (self._type.shortname, self._name)

    @property
    def longname(self):
        return '%s@%s' % (self._name, self._version)

    @property
    def latest_release(self):
        """Attempt retrieving the latest version number of a repository by 
        removing the staging and master branches.  If no version number is
        available, return 'master' since this is usually the latest stable
        version."""
        versions = list(self._known_versions.keys())

        if BRANCH_MASTER in versions:
            versions.remove(BRANCH_MASTER)
        if BRANCH_STAGING in versions:
            versions.remove(BRANCH_STAGING)
        
        if len(versions) > 0:
            versions = sorted(versions)
            return versions[-1]
        
        if BRANCH_MASTER in self._known_versions:
            return BRANCH_MASTER
        if BRANCH_STAGING in self._known_versions:
            return BRANCH_STAGING
        
        return self.version

    def is_downloaded(self):
        try:
            GitRepo(self._localdir)
            return True
        except InvalidGitRepositoryError:
            return False
    
    @property
    def short_source(self):
        """Determine the most succinct representation for the source and
        version for this repository.  Such that default origins from Github
        are 'minified'."""

        # TODO: This.  For now return the full source;
        return self._source

    @property
    def type(self):
        return self._type
    
    @property
    def git(self):
        return self._git
    
    @property
    def source(self):
        return self._source
    
    @property
    def localdir(self):
        return self._localdir
    
    @property
    def version(self):
        return self._version
    
    @property
    def known_versions(self):
        return self._known_versions
    
    @property
    def version_head(self):
        return self._version_head
    
    @property
    def last_updated(self):
        return self._last_updated
    
    @property
    def last_checked(self):
        return self._last_checked

    def intrusively_determine_kconfig(self):
        kconfig = None
        config_uk = UK_CONFIG_FILE % self._localdir
        if os.path.exists(config_uk):
            logger.debug("Reading: %s..." % config_uk)
            kconfig = kconfiglib.Kconfig(filename=config_uk)

        return kconfig
    
    def kconfig_enabled_flag(self):
        # No need to do anything for architecture, this one is weird
        if not (self._type is RepositoryType.ARCH or self._type is RepositoryType.CORE):
            kconfig = self.intrusively_determine_kconfig()

            # Retrieve the top-most item which enables the feature
            if kconfig.top_node.is_menuconfig:
                kconfig_item = kconfig.top_node.list.item.name
            else:
                kconfig_item = kconfig.top_node.list_item.name
            
            kconfig_item = KCONFIG % kconfig_item

            # Create a Yes enabled version of this repository
            return KCONFIG_EQ % (kconfig_item, KCONFIG_Y)
            
        return None
    
    @property
    def kconfig_extra(self):
        flatten = []

        for kconfig in self._kconfig_extra:
            flatten.append(KCONFIG_EQ % (kconfig, self._kconfig_extra[kconfig]))

        return flatten

    def __repr__(self):
        """Python representation"""
        return '<Repo %r>' % self._source

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
            if repository.name == key:
                return repository
    
        return default

    def all(self):
        return self._repositories

    def checkout(self):
        for repo in self.all():
            repo.repository.checkout()

    def update(self):
        for repo in self.all():
            repo.repository.update()
