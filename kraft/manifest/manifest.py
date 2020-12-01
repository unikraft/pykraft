# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Laboratories Europe Ltd., NEC Corporation.
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
import six
import sys
import uuid
import click
import semver
import pickle
import threading

from enum import Enum
from datetime import datetime
import dateutil.parser

from kraft.logger import logger

from kraft.const import UNIKRAFT_RELEASE_STABLE
from kraft.const import UNIKRAFT_RELEASE_STAGING
from kraft.const import UNIKRAFT_RELEASE_BRANCHES 

from kraft.error import KraftError
from kraft.error import UnknownVersionError
from kraft.error import UnknownVersionFormatError


class ManifestVersionEquality(Enum):
    EQ = ("==", "@")
    GT = (">=", "^")

    @classmethod
    def split(cls, name=None):
        if name is None or not isinstance(name, six.string_types):
            raise TypeError("name expected string")

        ret = None
        
        for eq in cls.__members__.items():
            for val in eq[1].value:
                if val in name:
                    parts = name.split(val)
                    ret = (parts[0], eq[1], val.join(parts[1:]))

        if not isinstance(ret, tuple):
            raise UnknownVersionFormatError(name)
        
        return ret

    @classmethod
    def eq(cls, name=None):
        name = ManifestVersionEquality.split(name)
        return True if name[1] is ManifestVersionEquality.EQ else False
    
    @classmethod
    def gt(cls, name=None):
        name = ManifestVersionEquality.split(name)
        return True if name[1] is ManifestVersionEquality.GT else False


class ManifestItemVersion(object):
    _version = None
    @property
    def version(self): return self._version
    
    _git_sha = None
    @property
    def git_sha(self): return self._git_sha

    _timestamp = None
    @property
    def timestamp(self): return self._timestamp

    _tarball = None
    @property
    def tarball(self): return self._tarball

    _tarball_size = None
    @property
    def tarball_size(self): return self._tarball_size

    _tarball_checksum = None
    @property
    def tarball_checksum(self): return self._tarball_checksum

    def __init__(self, **kwargs):
        self._version = kwargs.get('version', None)
        self._git_sha = kwargs.get('git_sha', None)
        self._timestamp = kwargs.get('timestamp', None)
        if self._timestamp is not None and isinstance(self._timestamp, six.string_types):
            self._timestamp = dateutil.parser.parse(self._timestamp)
        self._tarball = kwargs.get('tarball', None)
        self._tarball_size = kwargs.get('tarball_size', None)
        self._tarball_checksum = kwargs.get('tarball_checksum', None)

    def __str__(self):
        return "<ManifestItemVersion %s>" % (self._version)
    
    def __setstate__(self, state):
        if "meta" in state:
            meta = state["meta"]
            self._version = meta.get("name", None)

        if "data" in state:
            data = state["data"]
            self._git_sha = data.get("git_sha", None)
            self._timestamp = data.get("timestamp", None)
            if self._timestamp is not None and isinstance(self._timestamp, six.string_types):
                self._timestamp = dateutil.parser.parse(self._timestamp)
            self._tarball = data.get("tarball", None)
            self._tarball_size = data.get("tarball_size", None)
            self._tarball_checksum = data.get("tarball_checksum", None)
    
    def __getstate__(self):
        """
        Return state values to be pickled.
        """
        return {
            "meta": {
                "name": self._version
            },
            "data": {
                "git_sha": self._git_sha,
                "timestamp": str(self._timestamp),
                "tarball": self._tarball,
                "tarball_size": self._tarball_size,
                "tarball_checksum": self._tarball_checksum
            }
        }


class ManifestItemDistribution(object):
    _name = None
    @property
    def name(self): return self._name

    _manifest = None
    @property
    def manifest(self): return self._manifest

    _manifest_checksum = None
    @property
    def manifest_checksum(self): return self._manifest_checksum

    _latest = None
    @property
    def latest(self): return self._latest

    _versions = None
    @property
    def versions(self): return self._versions
    
    @latest.setter
    def latest(self, version=None):
        if version is None:
            return
        if not isinstance(version, ManifestItemVersion):
            raise TypeError("expected ManifestItemVersion")
        
        self._latest = version.version

    def __init__(self, **kwargs):
        self._manifest = kwargs.get('manifest', None)
        self._manifest_checksum = kwargs.get('manifest_checksum', None)
        self._name = kwargs.get('name', None)
        self.latest = kwargs.get('latest', None)

        if self.latest is not None \
            and not isinstance(self.latest, ManifestItemDistribution):
            raise TypeError("expected ManifestItemDistribution")

        elif kwargs.get("latest_version", None) is not None:
            self._latest = ManifestItemVersion(
                git_sha=kwargs["latest_git_sha"],
                version=kwargs["latest_version"],
                timestamp=kwargs.get("latest_timestamp", None),
                tarball=kwargs.get("latest_tarball", None),
                tarball_size=kwargs.get("latest_tarball_size", None),
                tarball_checksum=kwargs.get("latest_tarball_checksum", None)
            )
        
        self._versions = dict()
    
    def add_version(self, version=None):
        if isinstance(version, list):
            for i in version:
                self.add_version(i)
            return
        
        if not isinstance(version, ManifestItemVersion):
            raise TypeError("expected ManifestItemVersion")
            
        if version.version not in self.versions.keys():
            self._versions[version.version] = version
        
        if self._latest is None:
            self._latest = version
            return

        # This accounts for the fact that some unikraft releases are not
        # corresponding to semver, e.g. 0.4, and so we add an extra .0:
        current_version = version.version
        if current_version.count('.') == 1:
            current_version += ".0"

        latest_version = self._latest.version
        if latest_version.count('.') == 1:
            latest_version += ".0"

        try:
            if semver.compare(current_version, latest_version) > 0:
                self._latest = version

        # If not a semantic version, maybe it's a commit sha
        except ValueError:
            pass
    
    def get_version(self, version=None):
        if version in self._versions.keys():
            return self._versions[version]
        return None

    def __setstate__(self, state):
        if "meta" in state:
            meta = state["meta"]
            self._name = meta.get("name", None)
            self._manifest = meta.get("manifest", None)
            self._manifest_checksum = meta.get("manifest_checksum", None)

        if "data" in state:
            data = state["data"]
            if data.get("latest_version", None) is not None:
                self._latest = ManifestItemVersion(
                    git_sha=data["latest_git_sha"],
                    version=data["latest_version"],
                    timestamp=data.get("latest_timestamp", None),
                    tarball=data.get("latest_tarball", None),
                    tarball_size=data.get("latest_tarball_size", None),
                    tarball_checksum=data.get("latest_tarball_checksum", None)
                )

            versions = data.get("versions", None)
            if versions is not None:
                self._versions = dict()
                for d in versions:
                    version = ManifestItemVersion()
                    version.__setstate__(versions[d])
                    self._versions[d] = version

    def __getstate__(self):
        """
        Return state values to be pickled.
        """
        data = dict()
        if self._latest is not None:
            data["latest_git_sha"] = self._latest.git_sha
            data["latest_version"] = self._latest.version
            data["latest_timestamp"] = str(self._latest.timestamp)
            data["latest_tarball"] = self._latest.tarball
            data["latest_tarball_size "] = self._latest.tarball_size
            data["latest_tarball_checksum"] = self._latest.tarball_checksum

        if len(self._versions) > 0:
            data["versions"] = { 
                v: self._versions[v].__getstate__() for v in self._versions
            }

        return {
            "meta": {
                "name": self._name,
                "manifest": self._manifest,
                "manifest_checksum": self._manifest_checksum,
            },
            "data": data
        }


class ManifestItem(object):
    _name = None
    @property
    def name(self): return self._name

    _description = None
    @property
    def description(self): return self._description

    _type = None
    @property
    def type(self): return self._type

    _manifest = None
    @property
    def manifest(self): return self._manifest

    _manifest_checksum = None
    @property
    def manifest_checksum(self): return self._manifest_checksum

    _dists = None
    @property
    def dists(self): return self._dists

    _git = None
    @property
    def git(self): return self._git

    _last_checked = None
    @property
    def last_checked(self): return self._last_checked

    _provider = None
    @property
    def provider(self): return self._provider

    _localdir = None
    @property
    def localdir(self):
        """
        Determine the local directory for this manifest.  Essentially this
        uses the environmental variable for the respective type of component
        and appends the name.

        Returns:
            string: The directory on disk for the manifest.
        """
        if self._localdir is None:
            from kraft.types import str_to_component_type
            type = str_to_component_type(self.type)
            self._localdir = type.localdir(self.name)

        return self._localdir

    def __init__(self, **kwargs):
        self._name = kwargs.get('name', None)
        self._type = kwargs.get('type', None)
        self._description = kwargs.get('description', None)
        self._dists = kwargs.get('dists', dict())
        self._git = kwargs.get('git', None)
        self._last_checked = kwargs.get('last_checked', datetime.now())
        self._provider = kwargs.get('provider', None)
        self._manifest = kwargs.get('manifest', None)
        self._manifest_checksum = kwargs.get('manifest_checksum', None)
        self._localdir = kwargs.get('localdir', None)
    
    def add_distribution(self, dist=None):
        """
        Adds a distribution for this manifest since the manifest item may have
        different distributions.

        Args:
            dist (ManifestItemDistribution): The distribution of the item.
            dist (list): A list of distributions forthe item.
        """
        if isinstance(dist, list):
            for i in dist:
                self.add_distribution(i)
            return
        
        if not isinstance(dist, ManifestItemDistribution):
            raise TypeError("expected ManifestItemDistribution")
            
        if dist.name not in self.dists.keys():
            self._dists[dist.name] = dist
        
    def get_distribution(self, dist=None):
        if dist in self._dists.keys():
            return self._dists[dist]
        return None
    
    def get_version(self, version=None):
        if version in self._dists.keys():
            return self._dists[version].latest

        for dist in self._dists.keys():
            if version in self._dists[dist].versions.keys():
                return self._dists[dist].get_version(version)

        return None

    @click.pass_context
    def download(ctx, self, localdir=None, equality=ManifestVersionEquality.EQ,
            version=None, use_git=False, override_existing=False):
        dist = None

        # This accounts for the fact that some unikraft releases are not
        # corresponding to semver, e.g. 0.4, and so we add an extra .0:
        version_semver = version
        if version is not None and version.count('.') == 1:
            version_semver += ".0"

        # Select the distribution's latest if only the distribution is known 
        if version is not None and version in self._dists:
            dist = self._dists[version]
            version = dist.latest

        # Find the distribution based on the version
        elif version is not None and dist is None:
            for d in self._dists:
                if equality == ManifestVersionEquality.EQ:
                    if version in self._dists[d].versions:
                        dist = self._dists[d]
                        version = dist.versions[version]
                        break

                else:
                    for v in self._dists[d].versions:
                        # This accounts for the fact that some unikraft releases
                        # are not corresponding to semver, e.g. 0.4, and so we
                        # add an extra .0:
                        curr_semver = v
                        if curr_semver.count('.') == 1:
                            curr_semver += ".0"

                        try:
                            # This will ALSO select the distribution, based on
                            # whether the version matches or not. BE CAREFUL!
                            # e.g. staging@0.5 > stable@0.4
                            if semver.compare(curr_semver, version_semver) >= 0:
                                version_semver = curr_semver
                                dist = self._dists[d]
                                version = dist.versions[v]

                                # don't break here, keep iterating to find
                                # bigger and better versions.

                        # If not a semantic version, maybe it's a commit sha
                        except ValueError:
                            pass

        # Set stable as the default distribution and choose its latest version
        elif UNIKRAFT_RELEASE_STABLE in self._dists:
            dist = self._dists[UNIKRAFT_RELEASE_STABLE]
            version = dist.latest
        
        # Unknown version
        if dist is None or version is None:
            raise UnknownVersionError(version, self)

        if localdir is None:
            from kraft.types import str_to_component_type
            type = str_to_component_type(self._type)
            localdir = type.localdir(self.name)

        provider = self._provider.cls()
        provider.download(
            manifest=self,
            localdir=localdir,
            version=version,
            use_git=use_git,
            override_existing=override_existing
        )

    def __str__(self):
        return "%s/%s" % (self.type, self.name)
    
    def __setstate__(self, state):
        if "meta" in state:
            meta = state["meta"]
            self._name = meta.get("name", None)
            self._manifest = meta.get("manifest", None)
            self._manifest_checksum = meta.get("manifest_checksum", None)
            self._last_checked = meta.get("last_checked", None)
            if self._last_checked is not None:
                self._last_checked = dateutil.parser.parse(self._last_checked)
            self._provider = meta.get("provider", None)
            self._localdir = meta.get("localdir", None)
        
        if "data" in state:
            data = state["data"]
            self._description = data.get("description", None)
            self._type = data.get("type", None)
            
            dists = data.get("dists", None)
            if dists is not None:
                self._dists = dict()
                for d in dists:
                    dist = ManifestItemDistribution()
                    dist.__setstate__(dists[d])
                    self._dists[d] = dist
    
            self._git = data.get("git", None)
            
    def __getstate__(self):
        """
        Return state values to be pickled.
        """
        return {
            "meta": {
                "name": self._name,
                "manifest": self._manifest,
                "manifest_checksum": self._manifest_checksum,
                "last_checked": self._last_checked,
                "provider": self._provider,
                "localdir": self._localdir
            },
            "data": {
                "description": self._description,
                "type": self._type,
                "dists": { 
                    d: self._dists[d].__getstate__() for d in self._dists
                },
                "git": self._git
            }
        }


class Manifest(object):
    _manifest = None
    @property
    def manifest(self): return self._manifest

    _manifest_checksum = None
    @property
    def manifest_checksum(self): return self._manifest_checksum

    _items = None
    def items(self): return self._items.items()

    def __init__(self, **kwargs):
        self._manifest = kwargs.get('manifest', None)
        self._manifest_checksum = kwargs.get('manifest_checksum', None)
        self._items = dict()
        self._items_lock = threading.Lock()
        
    def add_item(self, item=None):
        if isinstance(item, list):
            for i in item:
                self.add_item(i)
            return
        
        if not isinstance(item, ManifestItem):
            raise TypeError("expected ManifestItem")

        with self._items_lock:
            # DO override existing item
            self._items[item.name] = item
    
    def get_item(self, item=None):
        if item in self._items.keys():
            return self._items[item]
        return None

    def __str__(self):
        return "<Manifest %s>" % (self._manifest)
    
    def __setstate__(self, state):
        if "meta" in state:
            meta = state["meta"]
            self._manifest = meta.get("manifest", None)
            self._manifest_checksum = meta.get("manifest_checksum", None)
        
        self._items = state.get("data", dict())
        self._items_lock = threading.Lock()
            
    def __getstate__(self):
        """
        Return state values to be pickled.
        """
        return {
            "meta": {
                "manifest": self._manifest,
                "manifest_checksum": self._manifest_checksum
            },
            "data": self._items
        }


class ManifestIndex(object):
    _index = dict()
    @property
    def all(self): return self._index

    def add_entry(self, checksum=None, url=None):
        if url in self.all.values():
            logger.warn("Manifest already in index")
            return
        
        self._index[checksum] = url


@click.pass_context
def maniest_from_name(ctx, name=None):
    from kraft.types import break_component_naming_format

    components = list()
    if name is None:
        return components

    type, name, _, _ = break_component_naming_format(name)

    for manifest_origin in ctx.obj.cache.all():
        manifest = ctx.obj.cache.get(manifest_origin)

        for _, component in manifest.items():
            if (type is None or \
                    (type is not None \
                        and type.shortname == component.type)) \
                    and component.name == name:
                components.append(component)

    return components

@click.pass_context
def manifest_from_localdir(ctx, localdir=None):
    if localdir is None or not os.path.isdir(localdir):
        return None

    for manifest_origin in ctx.obj.cache.all():
        manifest = ctx.obj.cache.get(manifest_origin)

        for _, component in manifest.items():
            if component.localdir == localdir:
                return component
    
    return None