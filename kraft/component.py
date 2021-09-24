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

import os
import shutil

import click
import kconfiglib
import six

from kraft.const import CONFIG_UK
from kraft.const import KCONFIG
from kraft.const import KCONFIG_EQ
from kraft.const import KCONFIG_Y
from kraft.const import MAKEFILE_UK
from kraft.const import UNIKRAFT_RELEASE_STABLE
from kraft.const import UNIKRAFT_RELEASE_STAGING
from kraft.error import DisabledComponentError
from kraft.error import MissingManifest
from kraft.error import UnknownVersionError
from kraft.logger import logger
from kraft.manifest import ManifestItemVersion
from kraft.manifest import ManifestVersionEquality
from kraft.types import ComponentType


class Component(object):
    """
    Components are the mission-critical repositories of a Unikraft project, this
    includes architectures, platforms, and libraries.   Each component has both
    the source code repository that defines its existence within a Unikraft
    project (namely, including files such as Makefile.uk, Config.uk and/or
    Linker.uk).  In addition to this, a component may have an origin repository
    which will contain external source code that has been patched and ported
    to Unikraft.  As a result, the Component object holds information about two
    different repositories as well as any configured semantics about the
    component, including its whereabouts on disk, what version it is at, etc.
    """
    _name = None

    @property
    def name(self): return self._name

    @name.setter
    def name(self, name=None): self._name = name

    _version = None

    @property
    def version(self):
        if self.is_downloaded:
            pass

        return self._version

    @version.setter
    def version(self, version): self._version = version

    _origin = None

    @property
    def origin(self): return self._origin

    _manifest = None

    @property
    def manifest(self): return self._manifest

    _description = None

    @property
    def description(self): return self._description

    _localdir = None

    @property
    @click.pass_context
    def localdir(ctx, self):
        if self._localdir is None and self._manifest is not None:
            self._localdir = self._manifest.localdir

        return self._localdir

    _kconfig_enabled_flag = None

    @property
    def kconfig_enabled_flag(self):
        if self._kconfig_enabled_flag is None:
            kconfig = self.intrusively_determine_kconfig()

            if kconfig is None:
                return None

            # Retrieve the top-most item which enables the feature
            if kconfig.top_node.is_menuconfig:
                kconfig_item = kconfig.top_node.list.item.name
            else:
                kconfig_item = kconfig.top_node.list_item.name

            if kconfig_item is None:
                return None

            kconfig_item = KCONFIG % kconfig_item

            # Create a Yes enabled version of this repository
            self._kconfig_enabled_flag = KCONFIG_EQ % (kconfig_item, KCONFIG_Y)
        return self._kconfig_enabled_flag

    _kconfig = None
    @property
    def kconfig(self): return self._kconfig

    _type = None
    @property
    def type(self): return self._type

    @click.pass_context  # noqa: C901
    def __init__(ctx, self, *args, **kwargs):
        self._name = kwargs.get("name", None)
        self._type = kwargs.get("type", self._type)
        self._manifest = kwargs.get("manifest", None)
        self._localdir = kwargs.get("localdir", None)
        ignore_version = kwargs.get("ignore_version", False)

        version = kwargs.get("version", None)
        config = kwargs.get("config", None)

        if isinstance(config, (six.string_types, int, float)):
            version = str(config)

        elif isinstance(config, dict):
            version = config.get("version", None)
            self._kconfig = config.get("kconfig", list())

        elif isinstance(config, bool) and config is False:
            raise DisabledComponentError(self._name)

        else:
            self._source = kwargs.get("source", None)
            self._kconfig = kwargs.get("kconfig", list())

        if self._manifest is None and self._type is not None:
            name = self._name
            if self._type is ComponentType.CORE:
                name = "unikraft"

            self._manifest = ctx.obj.cache.find_item_by_name(
                type=self._type.shortname,
                name=name
            )

        if self._manifest is None and self.localdir is not None:
            from kraft.manifest import manifest_from_localdir
            self._manifest = manifest_from_localdir(self._localdir)

        if self._manifest is not None:
            if self._name is None:
                self._name = self._manifest.name

            # Attempt to select the latest version from stable or staging
            if version is None:
                if UNIKRAFT_RELEASE_STABLE in self._manifest.dists.keys():
                    self._version = self._manifest.get_distribution(UNIKRAFT_RELEASE_STABLE).latest

                if self._version is None and UNIKRAFT_RELEASE_STAGING in self._manifest.dists.keys():
                    self._version = self._manifest.get_distribution(UNIKRAFT_RELEASE_STAGING).latest

            # Is the version actually a distribution name?
            elif version in self._manifest.dists.keys():
                self._version = \
                    self._manifest.get_distribution(version).latest

            # Maybe the version is from a distribution
            else:
                for dist in self._manifest.dists.keys():
                    dist = self._manifest.get_distribution(dist)
                    if version in dist.versions.keys():
                        self._version = dist.get_version(version)

            if self._version is None and ignore_version:
                known_versions = list()
                for dist in self._manifest.dists:
                    for ver in self._manifest.dists[dist].versions:
                        known_versions.append(self._manifest.dists[dist].versions[ver])

                # Select the only version available
                if len(known_versions) == 1:
                    self._version = known_versions[0]

            if self._version is None and not ignore_version:
                # TODO indicate component type in error message
                raise UnknownVersionError(version, self._manifest)

    @property
    def is_downloaded(self):
        return self.localdir is not None \
            and os.path.exists(self.localdir) \
            and os.path.exists(os.path.join(self.localdir, MAKEFILE_UK))

    def download(self, localdir=None, equality=ManifestVersionEquality.EQ,
                 use_git=False, override_existing=False):
        if self._manifest is None:
            raise MissingManifest(self._name)

        self._manifest.download(
            localdir=localdir,
            equality=equality,
            version=self._version,
            use_git=use_git,
            override_existing=override_existing
        )

    def intrusively_determine_kconfig(self):
        if self.is_downloaded:
            config_uk = os.path.join(self.localdir, CONFIG_UK)
            if os.path.exists(config_uk):
                logger.debug("Reading: %s..." % config_uk)
                return kconfiglib.Kconfig(filename=config_uk)

        return None

    def __str__(self):
        return "%s/%s@%s" % (self._type.shortname, self._name, self._version)

    def repr(self):
        config = {}

        if self.version is not None and \
                isinstance(self.version, ManifestItemVersion):
            config['version'] = self.version.version

        elif self.version is not None and \
                isinstance(self.version, six.string_types):
            config['version'] = self.version

        elif self.version is None and self.manifest is not None:
            if UNIKRAFT_RELEASE_STABLE in self._manifest.dists.keys():
                config['version'] = self._manifest.get_distribution(
                    UNIKRAFT_RELEASE_STAGING
                ).latest.version
            elif UNIKRAFT_RELEASE_STAGING in self._manifest.dists.keys():
                config['version'] = self._manifest.get_distribution(
                    UNIKRAFT_RELEASE_STAGING
                ).latest.version

        if self.origin is not None:
            config['source'] = self.origin

        if self._kconfig is not None and len(self._kconfig) > 0:
            config['kconfig'] = self._kconfig

        return True if not config else config


class ComponentManager(object):
    _components = []
    @property
    def components(self): return self._components
    def all(self): return self._components

    _cls = None
    @property
    def cls(self): return self._cls

    def __init__(self, components=[], cls=None, **extra):  # noqa:C901
        if cls is not None:
            self._cls = cls

        if self._cls is None:
            logger.critical("Cannot instantiate manager, missing cls: %s", self)
            return

        self._components = list()

        if isinstance(components, list):
            for component in components:
                if isinstance(component, self.cls):
                    self._components.append(component)
                else:
                    self._components.append(self.cls(
                        **component, **extra
                    ))

        elif isinstance(components, dict):
            self._components = list()

            for component, config in components.items():
                if isinstance(config, six.string_types):
                    inst = self.cls(
                        name=component,
                        version=config,
                    )
                elif isinstance(config, dict):
                    inst = self.cls(
                        name=component,
                        **config,
                        **extra
                    )
                self._components.append(inst)

        elif isinstance(components, object):
            self._components = list()
            self._components.append(components)

    def add(self, component=None):
        if component is None:
            raise ValueError("expected component")

        if not isinstance(component, Component):
            raise TypeError("expected Component")

        self._components.append(component)

    def remove(self, component=None, purge=False):
        if component is None:
            raise ValueError("expected component")

        if isinstance(component, six.string_types):
            for i, c in enumerate(self._components):
                if c.name == component:
                    if purge and os.path.exists(c.localdir):
                        logger.info("Purging lib/%s..." % component)
                        shutil.rmtree(c.localdir)

                    else:
                        logger.info("Removing lib/%s..." % component)

                    del self._components[i]

                    return True

        return False

    def get(self, name=None):
        for component in self._components:
            if component.name == name:
                return component
        return None

    def set(self, k, v):
        if k is not None:
            self._components[k] = v

    def repr(self):
        ret = {}
        for k in self.all():
            ret[k.name] = k.repr()

        return ret
