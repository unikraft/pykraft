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
import sys
from enum import Enum
from datetime import datetime
from kraft.logger import logger
from git.cmd import Git as GitCmd
from urllib.parse import urlparse
from kraft.component import KraftComponent
from git import Repo as GitRepo, RemoteProgress, InvalidGitRepositoryError, NoSuchPathError

BRANCH_MASTER="master"
BRANCH_STAGING="staging"

# Match against dereferenced tags only
# https://stackoverflow.com/a/15472310
GIT_TAG_PATTERN=re.compile(r'refs/tags/RELEASE-([\d\.]+)\^\{\}')
GIT_BRANCH_PATTERN=re.compile(r'refs/heads/(.*)')

class InvalidRepo(Exception):
    """The provided repository was not retrievable."""
    pass
class NoSuchReferenceInRepo(Exception):
    """The provided repository does not have the specified branch."""
    pass
class NoTypeAndNameRepo(Exception):
    """No type and name has been provided for this repository."""
    pass
class MismatchOriginRepo(Exception):
    """A repository with a different origin has been provided"""
    pass
class MismatchVersionRepo(Exception):
    """A repository with a different version has been provided"""
    pass

class Repo(object):
    name = None
    type = None

    remoteurl = None
    localdir = None

    current_version = None
    known_versions = {}
    git_branch = None
    git_commit = None

    last_updated = None
    last_checked = None

    def __init__(self, url):
        """Initialize a repository by reading from the remote URL"""

        if url is not None and len(url) > 0:
            if self.parse_url(url) is False:
                raise InvalidRepo

    def __init__(self,
        localdir=None,
        remoteurl=None,
        type=None,
        name=None,
        branch=None,
        tag=None,
        version=None,
        commit=None,
        force_update=False,
        download=False):
        """Initialize a repository by reading from the remote url."""

        if remoteurl is None or len(remoteurl) == 0:
            raise InvalidRepo

        self.remoteurl = remoteurl

        if type is not None:
            self.type = type

        if name is not None:
            self.name = name

        self.git_parse(
            localdir=localdir,
            remoteurl=remoteurl,
            branch=branch,
            tag=tag,
            commit=commit,
            force_update=force_update,
            download=download
        )

    def parse_url(self, remoteurl):
        """Determine the URL type and start the process of initializing this
        remote repository."""

        if self.parse_git(remoteurl=remoteurl):
            return True

        if self.parse_tarball(remoteurl=remoteurl):
            return True

        return False

    def git_remote_versions(self, remoteurl=None):
        """Determine a list of known versions for a repository by listing
        tags on a remote branch."""

        versions = {}

        if remoteurl is None:
            return versions

        g = GitCmd()

        logger.info("Probing %s..." % remoteurl)

        for refs in g.ls_remote(remoteurl).split('\n'):
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

    def git_parse(self,
        localdir=None,
        remoteurl=None,
        branch=BRANCH_STAGING,
        tag=None,
        commit=None,
        force_update=False,
        download=False):
        """Determine whether the provided URL is a Git repository and then
        remotely retrieve the contents of said repository based on yjr
        particular url and branch.  Returns boolean for success state of
        initializing the Repo object."""

        # Least accurate
        if branch is not None:
            self.git_branch = branch

        if commit is not None:
            self.git_commit = commit

        # In good scenarios, we have already been given key information about
        # this repository
        if self.type is None or self.name is None:
            # Let's passively determine the name and type first before we clone,
            # as this helps us determine where to place the repository when we
            # want to clone it.
            self.type, self.name = self.passively_determine_type_and_name(remoteurl)

        # Check if we already have a repository saved locally with this remote
        # url set.  If so, we do not need to make an outbound connection to
        # determine whether the repository is "real".
        if localdir is None:
            self.localdir = self.git_determine_localdir(type=self.type, name=self.name)
        else:
            self.localdir = localdir

        already_downloaded = False

        try:
            repo = GitRepo(self.localdir)
            already_downloaded = True
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            already_downloaded = False

        if already_downloaded is False or force_update:
            self.known_versions = self.git_remote_versions(remoteurl=self.remoteurl)

        # If there are no references it must not be a repository!
        if len(self.known_versions) == 0:
            raise InvalidRepo

        # Determine how to set the version
        if tag is not None and tag in self.known_versions:
            version = tag
        elif branch is not None and branch in self.known_versions:
            version = branch
        elif BRANCH_STAGING in self.known_versions:
            version = BRANCH_STAGING
        elif BRANCH_MASTER in self.known_versions:
            version = BRANCH_MASTER
        else:
            raise NoSuchReferenceInRepo

        # Deetermine the HEAD of the git repository
        if already_downloaded:
            # Is the repository object being instantiated with a different hash?
            if commit is not None and commit != repo.head.commit.hexsha and force_update:
                raise MismatchVersionRepo
            else:
                self.git_commit = repo.head.commit.hexsha
        else:
            self.git_commit = self.known_versions[version]

        # If we cannot determine the type passively, we must clone the
        # repository into a temporary location and manually introspect
        # the files to determine its type.
        if self.type is None or self.name is None:
            self.type, self.name = self.intrusively_determine_type_and_name(url)

        # If we cannot determine the name and type passively we must
        # throw an error and prompt the user for more information to
        # address this roblem.
        if self.type is None or self.name is None:
            raise NoTypeAndNameRepo

        if download or force_update:
            self.current_version = version

            if already_downloaded:
                self.git_update()

            elif download:
                logger.info("Downloading %s..." % str(self))
                r = GitRepo.clone_from(
                    url=self.remoteurl,
                    to_path=self.localdir,
                    multi_options=["--branch %s" % version]
                )
                self.last_updated = datetime.fromtimestamp(r.head.commit.committed_date)

        # This is a git repository
        return True

    def passively_determine_type_and_name(self, name):
        """Determine the name and type of the repository by checking the name of
        the repository against a well-known "type-name" syntax.  We can pass a
        name into this method, whether it's a URL, a directory or a name."""

        for type, member in KraftComponent.__members__.items():
            ref = member.search(name)

            if ref is not None:
                return member, ref.group(2)

        return None, None

    # TODO: Intrusively determine type and name from a remote URL by fetching
    # its contents.
    def intrusively_determine_type_and_name(self, remoteurl):
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

    def git_determine_localdir(self, type=None, name=None):
        """Sets the local directory for the repository based on the workspace
        setup which is detgermined by the environmental variables UK_WORKDIR,
        UK_ROOT, UK_LIBS or UK_APPS"""
        localdir = None

        if type is None or name is None:
            raise NoTypeAndNameRepo
            return False

        if type is KraftComponent.CORE:
            localdir = os.environ['UK_ROOT']

        elif type is KraftComponent.APP:
            localdir = os.path.join(os.environ['UK_APPS'], name)

        elif type is KraftComponent.LIB:
            localdir = os.path.join(os.environ['UK_LIBS'], name)

        # Platform is a special repository that is placed _within_ the core
        # unikraft repository for now.
        elif type is KraftComponent.PLAT:
            localdir = os.path.join(os.environ['UK_ROOT'], 'plat', name)

        return localdir

    def git_update(self):
        """Update this particular repository.  If this is a git repository, then
        we can simply attempt to fetch remote contents.  If this is a tarbell,
        we can attempt to re-download the sources.  However, this is likely not
        to work well since version numbers are usually embedded into the URL
        itself."""

        logger.info("Updating %s..." % str(self))

        r = GitRepo(self.localdir)
        valid_remote = None

        # Usually there is only 'origin', but let's iterate through all
        # origins just incase a developer has made local modifications to
        # the repo.
        for remote in r.remotes:
            for url in remote.urls:
                if url == self.remoteurl:
                    valid_remote = remote

        # We have been provided a different remote origin to the already
        # saved repository
        if valid_remote is None:
            raise MisMatchOriginRepo

        valid_remote.fetch()

        # TODO: Also set the last_updated field which is the timestamp of
        # latest commit of this selected version.

        self.last_checked = datetime.now()
        self.last_updated = datetime.fromtimestamp(r.head.commit.committed_date)

    def checkout(self, version=None):
        """Checkout a version of the repository."""

        if version is not None:
            logger.info("Using %s@%s..." % (self.shortname, version))
            r = GitRepo(self.localdir)
            r.git.checkout(version)
    
    @property
    def shortname(self):
        return '%s/%s' % (self.type.shortname, self.name)

    @property
    def longname(self):
        return '%s (%s@%s)' % (self.name, self.git_branch, self.git_commit[:8])

    @property
    def release(self):
        return self.git_commit[:8]

    def downloaded(self):
        return os.path.isdir(self.localdir)

    def __repr__(self):
        """Python representation"""
        return '<Repo %r>' % self.remoteurl

    def __str__(self):
        """String representation"""
        return self.longname
