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
import subprocess
import tempfile
from pathlib import Path

import click
import dpath.util as dpath_util
import six

import kraft.util as util
from kraft.arch import Architecture
from kraft.arch import InternalArchitecture
from kraft.component import Component
from kraft.config import Config
from kraft.config import find_config
from kraft.config import load_config
from kraft.config import SpecificationVersion
from kraft.config.config import get_default_config_files
from kraft.config.serialize import serialize_config
from kraft.const import DOT_CONFIG
from kraft.const import KRAFT_SPEC_LATEST
from kraft.const import MAKEFILE_UK
from kraft.const import SUPPORTED_FILENAMES
from kraft.const import UK_CORE_ARCHS
from kraft.const import UK_CORE_PLATS
from kraft.error import KraftFileNotFound
from kraft.error import MismatchTargetArchitecture
from kraft.error import MismatchTargetPlatform
from kraft.error import MissingComponent
from kraft.logger import logger
from kraft.manifest import ManifestItem
from kraft.plat import InternalPlatform
from kraft.plat import Platform
from kraft.plat import Runner
from kraft.unikraft import Unikraft


class Application(Component):
    _config = None
    @property
    def config(self): return self._config

    _core = None
    @property
    def core(self): return self._core

    _architectures = None
    @property
    def architectures(self): return self._architectures

    _platforms = None
    @property
    def platforms(self): return self._platforms

    _libraries = None
    @property
    def libraries(self): return self._libraries

    _runner = None
    @property
    def runner(self): return self._runner

    @click.pass_context  # noqa: C901
    def __init__(ctx, self, **kwargs):
        from kraft.types import ComponentType
        from kraft.cmd.list.update import kraft_update_from_source

        self._localdir = kwargs.get('localdir', None)
        self._name = kwargs.get('name', None)
        if self._name is None and self._localdir is not None:
            self._name = os.path.basename(self._localdir)
        self._config = kwargs.get('config', None)

        ignore_version = kwargs.get("ignore_version", False)

        # Deal with Unikraft component
        unikraft_config = dict()
        unikraft_manifest = None

        if self._config is None:
            unikraft_config = kwargs.get("unikraft", dict())

        elif isinstance(self._config, Config):
            unikraft_config = getattr(self._config, "unikraft")
            self._runner = Runner.from_config(self._config.runner)

        if isinstance(unikraft_config, ManifestItem):
            unikraft_manifest = unikraft_config
            unikraft_config = dict()

        else:
            unikraft_manifest = ctx.obj.cache.find_item_by_name(
                type="core", name="unikraft"
            )

        if unikraft_manifest is not None:
            self._core = Unikraft(
                name="unikraft",
                config=unikraft_config,
                manifest=unikraft_manifest,
                workdir=self.localdir,
                ignore_version=ignore_version
            )

        # Deal with other component types: {arch, plat, lib}
        for _, type in ComponentType.__members__.items():
            # Skip application-types or components with no manager
            if type.cls == self.__class__ or type.manager_cls is None:
                continue

            config = dict()
            components = None

            if self._config is None:
                config = kwargs.get(type.plural, dict())

            elif isinstance(self._config, Config):
                config = getattr(self._config, type.plural)

            if isinstance(config, type.manager_cls):
                components = config

            if isinstance(config, str):
                config = {config: True}

            elif isinstance(config, list):
                _config = dict()
                for c in config:
                    _config[c] = True
                config = _config

            if isinstance(config, dict):
                components = type.manager_cls([])
                for component in config.keys():
                    manifest = ctx.obj.cache.find_item_by_name(
                        type=type.shortname, name=component
                    )

                    if manifest is None and type == ComponentType.ARCH and \
                            component in UK_CORE_ARCHS and \
                            config[component] is not False:
                        components.add(InternalArchitecture(
                            core=self._core,
                            name=component,
                            config=config[component],
                            workdir=self.localdir
                        ))

                    elif manifest is None and type == ComponentType.PLAT and \
                            component in UK_CORE_PLATS and \
                            config[component] is not False:
                        components.add(InternalPlatform(
                            core=self._core,
                            name=component,
                            config=config[component],
                            workdir=self.localdir
                        ))

                    elif manifest is None:
                        source = None
                        if isinstance(config[component], dict):
                            source = config[component].get("source", None)

                        if source is None:
                            logger.warn("Unknown component: %s" % component)
                            continue

                        # Synchronously attempt to find the component
                        manifest = kraft_update_from_source(source)
                        if manifest is None:
                            logger.warn(
                                "Could not locate component %s from source: %s"
                                % (component, source))

                        elif len(manifest.items()) == 0 or \
                                manifest.get_item(component) is None:
                            logger.warn(
                                "Could not identify component %s at source: %s"
                                % (component, source))

                        else:
                            manifest = manifest.get_item(component)

                    if manifest is not None:
                        logger.debug("Adding component to app: %s" % manifest)
                        components.add(type.cls(
                            name=component,
                            config=config[component],
                            manifest=manifest,
                            workdir=self.localdir
                        ))

            if components is not None:
                setattr(self, "_%s" % type.plural, components)

        # Check the integrity of the application
        if self._core is None:
            raise MissingComponent("unikraft")

        if self._config is None:
            self._config = dict()

    @classmethod
    @click.pass_context
    def from_workdir(ctx, cls, workdir=None, force_init=False):
        if workdir is None:
            workdir = ctx.obj.workdir

        config = None
        try:
            config = load_config(find_config(workdir, None, ctx.obj.env))
        except KraftFileNotFound:
            pass

        return cls(
            config=config,
            localdir=workdir,
            ignore_version=force_init,
        )

    @property
    def components(self):
        from kraft.types import ComponentType

        components = list()

        components.append(self._core)

        for _, type in ComponentType.__members__.items():
            # Skip application-types or components with no manager
            if type.cls == self.__class__ or type.manager_cls is None:
                continue

            manager = getattr(self, "_%s" % type.plural)

            for component in manager.components:
                components.append(component)

        return components

    @property
    def manifests(self):
        manifests = list()
        components = self.components

        for component in components:
            if component.manifest is not None:
                manifests.append(component.manifest)

        return manifests

    def is_configured(self):
        if os.path.exists(os.path.join(self._localdir, DOT_CONFIG)) is False:
            return False

        return True

    def open_menuconfig(self):
        """
        Run the make menuconfig target.
        """
        cmd = self.make_raw('menuconfig')
        logger.debug("Running:\n%s" % ' '.join(cmd))
        subprocess.run(cmd)

    def make_raw(self, extra=None, verbose=False):
        """
        Return a string with a correctly formatted make entrypoint for this
        application.
        """

        cmd = [
            'make',
            '-C', self._core.localdir,
            ('A=%s' % self._localdir)
        ]

        if verbose:
            cmd.append('V=1')

        plat_paths = []
        for plat in self._platforms.all():
            if not isinstance(plat, InternalPlatform):
                plat_paths.append(plat.localdir)

        cmd.append('P=%s' % ":".join(plat_paths))

        lib_paths = []
        for lib in self._libraries.all():
            lib_paths.append(lib.localdir)

        cmd.append('L=%s' % ":".join(lib_paths))

        if type(extra) is list:
            for i in extra:
                cmd.append(i)

        elif type(extra) is str:
            cmd.append(extra)

        return cmd

    @click.pass_context
    def make(ctx, self, extra=None):
        """
        Run a make target for this project.
        """
        cmd = self.make_raw(
            extra=extra, verbose=ctx.obj.verbose
        )
        util.execute(cmd)

    @click.pass_context  # noqa: C901
    def configure(ctx, self, arch=None, plat=None, options=[],
                  force_configure=False):
        """
        Configure a Unikraft application.
        """

        if not self.is_configured():
            self.init()

        archs = list()
        if isinstance(arch, str):
            _arch = self.architectures.get(arch)
            if _arch is None:
                raise MismatchTargetArchitecture(arch, [
                    a.name for a in self.architectures.all()
                ])
            archs.append(_arch)

        elif isinstance(arch, Architecture):
            archs.append(arch)

        elif isinstance(arch, list):
            archs = arch
        else:
            archs = self.architectures.all()

        plats = list()
        if isinstance(plat, str):
            _plat = self.platforms.get(plat)
            if _plat is None:
                raise MismatchTargetPlatform(plat, [
                    a.name for a in self.platforms.all()
                ])
            plats.append(_plat)

        elif isinstance(plat, Platform):
            plats.append(plat)

        elif isinstance(plat, list):
            plats = plat
        else:
            plats = self.platforms.all()

        # Generate a dynamic .config to populate defconfig with based on
        # configure's parameterization.
        dotconfig = self._core.kconfig

        for arch in archs:
            if not arch.is_downloaded():
                raise MissingComponent(arch.name)

            dotconfig.extend(arch.kconfig)
            dotconfig.append(arch.kconfig_enabled_flag)

        for plat in plats:
            if not plat.is_downloaded():
                raise MissingComponent(plat.name)

            dotconfig.extend(plat.kconfig)
            dotconfig.append(plat.kconfig_enabled_flag)

        for lib in self.libraries.all():
            if not lib.is_downloaded():
                raise MissingComponent(lib.name)

            dotconfig.extend(lib.kconfig)
            dotconfig.append(lib.kconfig_enabled_flag)

        # Add any additional confguration options, and overriding existing
        # configuraton options.
        for new_opt in options:
            o = new_opt.split('=')
            for exist_opt in dotconfig:
                e = exist_opt.split('=')
                if o[0] == e[0]:
                    dotconfig.remove(exist_opt)
                    break
            dotconfig.append(new_opt)

        # Create a temporary file with the kconfig written to it
        fd, path = tempfile.mkstemp()

        with os.fdopen(fd, 'w+') as tmp:
            logger.debug('Using the following defconfig:')
            for line in dotconfig:
                logger.debug(' > ' + line)
                tmp.write(line + '\n')

        try:
            self.make([
                ('UK_DEFCONFIG=%s' % path),
                'defconfig'
            ])
        finally:
            os.remove(path)

    @click.pass_context
    def add_arch(ctx, self, arch=None):
        from kraft.types import ComponentType
        self.add_component(ComponentType.ARCH, arch)

    @click.pass_context
    def add_plat(ctx, self, plat=None):
        from kraft.types import ComponentType
        self.add_component(ComponentType.PLAT, plat)

    @click.pass_context
    def add_lib(ctx, self, lib=None):
        from kraft.types import ComponentType
        return self.add_component(ComponentType.LIB, lib)

    @click.pass_context
    def add_component(ctx, self, type=None, component=None):
        from kraft.manifest import maniest_from_name

        components = list()

        if component is None or str(component) == "":
            logger.warn("No component to add")
            return False

        elif isinstance(component, six.string_types):
            from kraft.types import break_component_naming_format
            _, name, _, version = break_component_naming_format(component)
            manifests = maniest_from_name(component)
            if len(manifests) == 0:
                logger.warn("Unknown component: %s" % component)
                return False

            for manifest in manifests:
                components.append(type.cls(
                    name=name,
                    version=version,
                    manifest=manifest,
                ))

        elif isinstance(component, (dict, list)):
            return self.add_component(type, list(component))

        elif isinstance(component, Component):
            components.append(component)

        manager = getattr(self, "_%s" % type.plural)
        for component in components:
            manager.add(component)

        self.save_yaml()

        return True

    @click.pass_context
    def build(ctx, self, fetch=True, prepare=True, target=None, n_proc=0):
        extra = []
        if n_proc is not None and n_proc > 0:
            extra.append('-j%s' % str(n_proc))

        if not fetch and not prepare:
            fetch = prepare = True

        if fetch:
            self.make('fetch')

        if prepare:
            self.make('prepare')

        # Create a no-op when target is False
        if target is False:
            return

        elif target is not None:
            extra.append(target)

        self.make(extra)

    def init(self, create_makefile=False, force_create=False):
        """
        Initialize an app component's directory.
        """
        makefile_uk = os.path.join(self.localdir, MAKEFILE_UK)
        if os.path.exists(makefile_uk) is False or force_create:
            logger.debug("Creating: %s" % makefile_uk)
            Path(makefile_uk).touch()

        if create_makefile:
            pass

        try:
            filenames = get_default_config_files(self.localdir)
        except KraftFileNotFound:
            filenames = []

        if len(filenames) == 0 or force_create:
            self.save_yaml()

    def clean(self, proper=False):
        """
        Clean the application.
        """

        if proper:
            self.make("properclean")

        else:
            self.make("clean")

    def repr(self):
        config = {
            'name': self.name,
            'unikraft': self.core.repr()
        }

        if self.config is None or not isinstance(self.config, Config):
            config['specification'] = SpecificationVersion(
                KRAFT_SPEC_LATEST
            )
        else:
            config['specification'] = self.config.specification

        for arch in self.architectures.all():
            dpath_util.new(
                config,
                'architectures/%s' % arch.name,
                arch.repr()
            )

        for plat in self.platforms.all():
            dpath_util.new(
                config,
                'platforms/%s' % plat.name,
                plat.repr()
            )

        for lib in self.libraries.all():
            dpath_util.new(
                config,
                'libraries/%s' % lib.name,
                lib.repr()
            )

        if "libraries" not in config:
            config["libraries"] = {}

        if self.runner is not None:
            config['runner'] = self.runner.repr()
        else:
            config['runner'] = {}

        return Config(**config)

    def to_yaml(self):
        """
        Return a YAML with the serialized string of this object.
        """
        return serialize_config(self.repr())

    def save_yaml(self, file=None):
        if file is None:
            file = os.path.join(self.localdir, SUPPORTED_FILENAMES[0])

        logger.debug("Saving: %s" % file)
        with open(file, 'w+') as f:
            yaml = self.to_yaml()
            f.write(yaml)
