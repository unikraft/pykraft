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
import uuid
import functools
import kconfiglib

from enum import Enum
from datetime import datetime
from urllib.parse import urlparse

from git import RemoteProgress
from git import NoSuchPathError
from git import GitCommandError
from git import Repo as GitRepo
from git.cmd import Git as GitCmd
from git.exc import GitCommandError
from git import InvalidGitRepositoryError

from kraft.components.provider import ProviderType
from kraft.components.provider.git import GitProvider
from kraft.components.provider import determine_provider

from kraft.logger import logger

from kraft.kraft import kraft_context

from kraft.errors import NoTypeAndNameRepo
from kraft.errors import NoSuchReferenceInRepo
from kraft.errors import UnknownSourceProvider
from kraft.errors import InvalidRepositoryFormat
from kraft.errors import InvalidRepositorySource

from kraft.constants import KCONFIG
from kraft.constants import KCONFIG_Y
from kraft.constants import KCONFIG_EQ
from kraft.constants import BRANCH_MASTER
from kraft.constants import CONFIG_UK_LIB
from kraft.constants import UNIKRAFT_CORE
from kraft.constants import UK_CONFIG_FILE
from kraft.constants import CONFIG_UK_PLAT
from kraft.constants import BRANCH_STAGING

from kraft.components.types import RepositoryType

from atpbar import atpbar, find_reporter

class GitProgressPrinter(RemoteProgress):
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

class Repository(object):
    _name = None
    _type = None

    _git = None
    _source = None
    _localdir = None
    _provider = None

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
        provider=None,
        repository_type=None,
        force_update=False,
        download=False,
        kconfig_extra={}):
        """Determine whether the provided URL is a Git repository and then
        remotely retrieve the contents of said repository based on your
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

        # Determine provider
        if provider is None:
            provider = determine_provider(source)
            
            if provider is None:
                raise UnknownSourceProvider(source)

        self.provider = provider
    
        if len(self.known_versions) == 0 or force_update or download:
            self.known_versions = self.provider.probe_remote_versions()
            self.last_checked = datetime.now()

        # Determine how to set the version
        if version is not None:
            self.version = version
        elif BRANCH_MASTER in self.known_versions:
            self.version = BRANCH_MASTER
        elif BRANCH_STAGING in self.known_versions:
            self.version = BRANCH_STAGING
        else:
            self.version = None

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
            self.localdir = self.determine_localdir(source=source, repository_type=repository_type, name=name)
        else:
            self.localdir = localdir

        # Populate the repository information if we have made it this far, as it
        # means that the repository is valid and usable.
        self.name = name
        self.type = repository_type
        self.source = source
        self.kconfig_extra = kconfig_extra

        if download or force_update:
            self.update()
        
        if self.type == RepositoryType.ARCH:
            return
        
        elif self.type == RepositoryType.PLAT and self.source == UNIKRAFT_CORE:
            return
        
        # self._set_cache(source, self)
        
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
        # elif kwargs['repository_type'] == RepositoryType.ARCH:
        #     return super(Repository, cls).__new__(cls)
        # elif kwargs['repository_type'] == RepositoryType.PLAT and kwargs['source'] == UNIKRAFT_CORE:
        #     return super(Repository, cls).__new__(cls)
        
        existing = None
        source = kwargs['source']
        if not source.startswith("file://"):
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

    @kraft_context
    def determine_localdir(ctx, self, source=None, repository_type=None, name=None):
        """Sets the local directory for the repository based on the workspace
        setup which is detgermined by the environmental variables UK_WORKDIR,
        UK_ROOT, UK_LIBS or UK_APPS"""
        localdir = None

        if repository_type is None or name is None:
            raise NoTypeAndNameRepo
            return False
        
        if source.startswith("file://"):
            localdir = os.path.join(ctx.workdir, source[len("file://"):])

        elif repository_type is RepositoryType.CORE:
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
            repo = GitRepo(self.localdir)
        
        # Not a repository? No problem, let's clone it:
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            repo = GitRepo.init(self.localdir)
            repo.create_remote('origin', self.source)

        try:
            if sys.stdout.isatty():
                repo.remotes.origin.fetch(progress=GitProgressPrinter(label=self.longname))
            else:
                for fetch_info in repo.remotes.origin.fetch():
                    logger.debug("Updated %s %s to %s" % (self.source, fetch_info.ref, fetch_info.commit))
            
            self.last_checked = datetime.now()
        except (GitCommandError, AttributeError) as e:
            logger.error("Could not fetch %s: %s" % (self.source, str(e)))
        
        # self.checkout(self.version)
        # self.last_updated = datetime.fromtimestamp(repo.head.commit.committed_date)

    @kraft_context
    def checkout(ctx, self, version=None, retry=False):
        """Checkout a version of the repository."""

        if ctx.dont_checkout:
            return

        if version is None:
            version = self.version

        if self.type == RepositoryType.ARCH:
            return
        elif self.type == RepositoryType.PLAT and self.source == UNIKRAFT_CORE:
            return
        elif version is not None:
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
                
                # Determine if the repository has already been checked out at
                # this version
                if commit_hash.startswith(version) \
                or version in self.known_versions.keys() and self.known_versions[version] == commit_hash:
                    logger.debug("%s already at %s" % (self.name, version))
                    return
            except ValueError as e:
                pass

            logger.debug("Checking-out %s@%s..." % (self.name, version))

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
                            logger.error("Could not checkout %s@%s: %s" % (self.name, version, str(e2)))
                            sys.exit(1)
                elif not ctx.ignore_checkout_errors:
                    logger.error("Could not checkout %s@%s: %s" % (self.name, version, str(e1)))
                    sys.exit(1)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
    
    @property
    def shortname(self):
        return '%s/%s' % (self.type.shortname, self.name)

    @property 
    def libname(self):
        name = self.name.lower()

        if name.startswith('lib-'):
            return name
        
        return 'lib-%s' % name 
    
    @property 
    def kname(self):
        name = self.name.upper()

        if name.startswith('LIB'):
            return name
        
        return 'LIB%s' % name 

    @property
    def type(self):
        return self._type
        
    @type.setter
    def type(self, type):
        self._type = type
    
    @property
    def git(self):
        return self._git

    @git.setter
    def git(self, git):
        self._git = git
    
    @property
    def longname(self):
        return '%s/%s@%s' % (self.type.shortname, self.name, self.latest_release)
    
    @property
    def source(self):
        return self._source
    
    @source.setter
    def source(self, source):
        self._source = source
    
    @property
    def localdir(self):
        return self._localdir
    
    @localdir.setter
    def localdir(self, localdir):
        self._localdir = localdir
    
    @property
    def provider(self):
        return self._provider
    
    @provider.setter
    def provider(self, provider):
        self._provider = provider
    
    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, version):
        self._version = version
    
    @property
    def known_versions(self):
        return self._known_versions
    
    @known_versions.setter
    def known_versions(self, known_versions):
        self._known_versions = known_versions
    
    @property
    def version_head(self):
        return self._version_head
    
    @version_head.setter
    def version_head(self, version_head):
        self._version_head = version_head
    
    @property
    def last_updated(self):
        return self._last_updated
    
    @last_updated.setter
    def last_updated(self, last_updated):
        self._last_updated = last_updated
    
    @property
    def last_checked(self):
        return self._last_checked
    
    @last_checked.setter
    def last_checked(self, last_checked):
        self._last_checked = last_checked

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
            versions = sorted(versions)
            return versions[-1]
        
        if BRANCH_MASTER in self.known_versions:
            return BRANCH_MASTER
        if BRANCH_STAGING in self.known_versions:
            return BRANCH_STAGING
        
        return self.version

    def is_downloaded(self):
        try:
            GitRepo(self.localdir)
            return True
        except InvalidGitRepositoryError:
            return False
    
    @property
    def short_source(self):
        """Determine the most succinct representation for the source and
        version for this repository.  Such that default origins from Github
        are 'minified'."""

        # TODO: This.  For now return the full source;
        return self.source

    def intrusively_determine_kconfig(self):
        kconfig = None
        config_uk = UK_CONFIG_FILE % self.localdir
        
        if os.path.exists(config_uk):
            logger.debug("Reading: %s..." % config_uk)
            kconfig = kconfiglib.Kconfig(filename=config_uk)

        return kconfig
    
    def kconfig_enabled_flag(self):
        # No need to do anything for architecture, this one is weird
        if not (self.type is RepositoryType.ARCH or self.type is RepositoryType.CORE):
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
    
    @kconfig_extra.setter
    def kconfig_extra(self, kconfig_extra={}):
        self._kconfig_extra = kconfig_extra

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
