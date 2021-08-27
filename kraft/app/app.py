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
import tarfile
import tempfile
from pathlib import Path

import click
import requests
import six

import kraft.util as util
from kraft.arch import Architecture
from kraft.component import Component
from kraft.config import Config
from kraft.config import find_config
from kraft.config import load_config
from kraft.config.config import get_default_config_files
from kraft.config.serialize import serialize_config
from kraft.const import DOT_CONFIG
from kraft.const import MAKEFILE_UK
from kraft.const import SUPPORTED_FILENAMES
from kraft.const import UK_CORE_ARCHS
from kraft.const import UK_CORE_PLATS
from kraft.const import UNIKRAFT_BUILDDIR
from kraft.const import UNIKRAFT_LIB_MAKEFILE_URL_EXT
from kraft.error import KraftError
from kraft.error import KraftFileNotFound
from kraft.error import MissingComponent
from kraft.lib import Library
from kraft.lib import LibraryManager
from kraft.logger import logger
from kraft.manifest import maniest_from_name
from kraft.plat import InternalPlatform
from kraft.plat import Platform
from kraft.plat.network import NetworkManager
from kraft.plat.volume import VolumeDriver
from kraft.plat.volume import VolumeManager
from kraft.target import Target
from kraft.target import TargetManager
from kraft.types import break_component_naming_format
from kraft.types import ComponentType
from kraft.unikraft import Unikraft


class Application(Component):
    _type = ComponentType.APP

    _config = None
    @property
    def config(self): return self._config

    @click.pass_context  # noqa: C901
    def __init__(ctx, self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)

        self._config = kwargs.get('config', None)
        self._name = kwargs.get('name', None)

        # Determine name from localdir
        if self._name is None and self._localdir is not None:
            self._name = os.path.basename(self._localdir)

        # Determine how configuration is passed to this class
        if self._config is None:
            unikraft = kwargs.get("unikraft", dict())
            if not isinstance(unikraft, Unikraft):
                unikraft = Unikraft(unikraft)

            targets = kwargs.get("targets", TargetManager([
                Target(
                    architecture=UK_CORE_ARCHS[0],
                    platform=UK_CORE_PLATS[0]
                )
            ]))
            if not isinstance(targets, TargetManager):
                targets = TargetManager(targets)

            libraries = kwargs.get("libraries", dict())
            if not isinstance(unikraft, LibraryManager):
                libraries = LibraryManager(libraries)

            networks = kwargs.get("networks", dict())
            if not isinstance(networks, NetworkManager):
                networks = NetworkManager(networks)

            volumes = kwargs.get("volumes", dict())
            if not isinstance(volumes, VolumeManager):
                volumes = VolumeManager(volumes)

            self._config = Config(
                name=kwargs.get('name', self._name),
                arguments=kwargs.get("arguments", None),
                before=kwargs.get("before", None),
                after=kwargs.get("after", None),
                unikraft=unikraft,
                targets=targets,
                libraries=libraries,
                volumes=volumes,
                networks=networks,
            )

        if self.config.name is None:
            self.config.name = self._name

        # Check the integrity of the application
        if self.config.unikraft is None:
            raise MissingComponent("unikraft")

        # Initialize the location of the known binaries
        for target in self.config.targets.all():
            binname = target.binary_name(self.config.name)
            binary = os.path.join(self.localdir, UNIKRAFT_BUILDDIR, binname)
            if binname is not None:
                target.binary = binary

        if self._config is None:
            self._config = dict()

    @classmethod  # noqa: C901
    @click.pass_context
    def from_workdir(ctx, cls, workdir=None, force_init=False, use_versions=[]):
        if workdir is None:
            workdir = ctx.obj.workdir

        config = load_config(
            find_config(workdir, None, ctx.obj.env),
            use_versions=use_versions
        )

        return cls(
            config=config,
            localdir=workdir,
            ignore_version=force_init,
        )

    @property
    def components(self):
        components = list()

        components.append(self.config.unikraft)

        for target in self.config.targets.all():
            components.append(target.architecture)
            components.append(target.platform)

        for library in self.config.libraries.all():
            components.append(library)

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
            '-C', self.config.unikraft.localdir,
            ('A=%s' % self._localdir)
        ]

        if verbose:
            cmd.append('V=1')

        plat_paths = []
        for target in self.config.targets.all():
            if not isinstance(target.platform, InternalPlatform):
                plat_paths.append(target.platform.localdir)

        if len(plat_paths) > 0:
            cmd.append('P=%s' % ":".join(plat_paths))

        lib_paths = []
        for lib in self.config.libraries.all():
            lib_paths.append(lib.localdir)

        cmd.append('L=%s' % ":".join(lib_paths))

        if type(extra) is list:
            for i in extra:
                cmd.append(i)

        elif type(extra) is str:
            cmd.append(extra)

        return cmd

    @click.pass_context
    def make(ctx, self, extra=None, verbose=False):
        """
        Run a make target for this project.
        """
        cmd = self.make_raw(
            extra=extra, verbose=verbose
        )
        return util.execute(cmd)

    @click.pass_context  # noqa: C901
    def configure(ctx, self, target=None, arch=None, plat=None, options=[],
                  force_configure=False):
        """
        Configure a Unikraft application.
        """

        if not self.is_configured():
            self.init()

        if target is not None and isinstance(target, Target):
            arch = target.architecture
            plat = target.platform

        archs = list()
        plats = list()

        def match_arch(arch, target):
            if isinstance(arch, six.string_types) and \
                    arch == target.architecture.name:
                return target.architecture
            if isinstance(arch, Architecture) and \
                    arch.name == target.architecture.name:
                return arch
            return None

        def match_plat(plat, target):
            if isinstance(plat, six.string_types) and \
                    plat == target.platform.name:
                return target.platform
            if isinstance(plat, Platform) and \
                    plat.name == target.platform.name:
                return plat
            return None

        if len(self.config.targets.all()) == 1 \
                and target is None and arch is None and plat is None:
            target = self.config.targets.all()[0]
            archs.append(target.architecture)
            plats.append(target.platform)

        else:
            for t in self.config.targets.all():
                if match_arch(arch, t) is not None \
                        and match_plat(plat, t) is not None:
                    archs.append(t.architecture)
                    plats.append(t.platform)

        # Generate a dynamic .config to populate defconfig with based on
        # configure's parameterization.
        dotconfig = list()
        dotconfig.extend(self.config.unikraft.kconfig or [])

        for arch in archs:
            if not arch.is_downloaded:
                raise MissingComponent(arch)

            dotconfig.extend(arch.kconfig)
            dotconfig.append(arch.kconfig_enabled_flag)

        for plat in plats:
            if not plat.is_downloaded:
                raise MissingComponent(plat)

            dotconfig.extend(plat.kconfig)
            dotconfig.append(plat.kconfig_enabled_flag)

        for lib in self.config.libraries.all():
            if not lib.is_downloaded:
                raise MissingComponent(lib)

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

        return_code = 0

        try:
            return_code = self.make([
                ('UK_DEFCONFIG=%s' % path),
                'defconfig'
            ])
        finally:
            os.remove(path)

        if return_code > 0:
            raise KraftError("Could not configure application")

        return True

    @click.pass_context
    def add_lib(ctx, self, lib=None):
        if lib is None or str(lib) == "":
            logger.warn("No library to add")
            return False

        elif isinstance(lib, six.string_types):
            _, name, _, version = break_component_naming_format(lib)
            manifests = maniest_from_name(name)

            if len(manifests) == 0:
                logger.warn("Unknown library: %s" % lib)
                return False

            for manifest in manifests:
                if manifest.type != ComponentType.LIB:
                    continue

                logger.info("Adding %s@%s" % (manifest, version))
                self.config.libraries.add(Library(
                    name=name,
                    version=version,
                    manifest=manifest,
                ))

        self.save_yaml()

        return True

    @click.pass_context
    def build(ctx, self, target=None, n_proc=0, verbose=False):
        extra = []
        if n_proc is not None and n_proc > 0:
            extra.append('-j%s' % str(n_proc))

        # Create a no-op when target is False
        if target is False:
            return

        elif target is not None:
            extra.append(target)

        return self.make(extra, verbose)

    def list_possible_mirrors(self):
        extra = []
        for lib in self.config.libraries.all():
            if not lib.is_fetched:
                for mirror in lib.origin_mirrors:
                    try:
                        response = requests.head(mirror)

                    except Exception:
                        logger.debug("Mirror down: %s" % mirror)
                        break

                    if response.status_code == 200:
                        extra.append(
                            lib.kname +
                            UNIKRAFT_LIB_MAKEFILE_URL_EXT +
                            "=" +
                            mirror
                        )
                    else:
                        logger.debug("Mirror down: %s" % mirror)
                        break
        return extra

    @click.pass_context
    def fetch(ctx, self, verbose=False):
        extra = []

        if ctx.obj.settings.fetch_prioritize_origin is False:
            extra.extend(self.list_possible_mirrors())

        extra.append('fetch')

        return self.make(extra, verbose)

    @click.pass_context
    def prepare(ctx, self, verbose=False):
        return self.make('prepare', verbose)

    def init(self, create_makefile=False, force_create=False):
        """
        Initialize an app component's directory.
        """

        if os.path.exists(self.localdir) is False or force_create:
            logger.debug("Creating: %s" % self.localdir)
            Path(self.localdir).mkdir(parents=True, exist_ok=True)

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

    def run(self, target=None, initrd=None, background=False,  # noqa: C901
            paused=False, gdb=4123, dbg=False, virtio_nic=None, bridge=None,
            interface=None, dry_run=False, args=None, memory=64, cpu_sockets=1,
            cpu_cores=1):

        if target is None:
            raise KraftError('Target not set')

        elif target.binary is None:
            raise KraftError('Target has not been compiled')

        elif not os.path.exists(target.binary):
            raise KraftError('Could not find unikernel: %s' % target.binary)

        logger.debug("Running binary: %s" % target.binary)

        runner = target.platform.runner
        runner.use_debug = dbg
        runner.architecture = target.architecture.name

        if initrd:
            runner.add_initrd(initrd)

        if virtio_nic:
            runner.add_virtio_nic(virtio_nic)

        if bridge:
            runner.add_bridge(bridge)

        if interface:
            runner.add_interface(interface)

        if gdb:
            runner.open_gdb(gdb)

        if isinstance(memory, int) and memory > 0:
            runner.set_memory(memory)

        if cpu_sockets:
            runner.set_cpu_sockets(cpu_sockets)

        if cpu_cores:
            runner.set_cpu_cores(cpu_cores)

        for volume in self.config.volumes.all():
            if volume.driver is VolumeDriver.VOL_9PFS:
                path = os.path.join(self.localdir, volume.name)

                if not os.path.exists(path):
                    tar = tarfile.open(volume.source)
                    tar.extractall(path)
                    tar.close()

                runner.add_virtio_9pfs(path)

        runner.unikernel = target.binary
        runner.execute(
            extra_args=args,
            background=background,
            paused=paused,
            dry_run=dry_run,
        )

    def clean(self, proper=False):
        """
        Clean the application.
        """

        if proper:
            self.make("properclean")

        else:
            self.make("clean")

    @property
    def binaries(self):
        binaries = []

        for target in self.config.targets.all():
            if target.binary is not None:
                binaries.append(target)

        return binaries

    def repr(self):
        return self.config

    def save_yaml(self, file=None):
        if file is None:
            file = os.path.join(self.localdir, SUPPORTED_FILENAMES[0])

        yaml = serialize_config(
            self.repr(),
            original=file
        )

        logger.debug("Saving: %s" % file)

        with open(file, 'w+') as f:
            f.write(yaml)
