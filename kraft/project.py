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

import re
import os
import sys
import json
import tempfile
import kconfiglib
import subprocess
import dpath.util as dpath_util
from pathlib import Path
from json.decoder import JSONDecodeError

from kraft.logger import logger
from kraft.kraft import kraft_context

from kraft.components import Core
from kraft.components import Volume
from kraft.components import Volumes
from kraft.components import Network
from kraft.components import Networks
from kraft.components import Library
from kraft.components import Libraries
from kraft.components import Platform
from kraft.components import Platforms
from kraft.components import Architecture
from kraft.components import Architectures
from kraft.components import Repository
from kraft.types import RepositoryType

from kraft.errors import CannotReadDepsJson
from kraft.errors import InvalidRepositorySource
from kraft.errors import MisconfiguredUnikraftProject
from kraft.errors import MismatchTargetArchitecture
from kraft.errors import MismatchTargetPlatform

import kraft.util as util
from kraft.constants import KCONFIG_Y
from kraft.constants import DEPS_JSON
from kraft.constants import DOT_CONFIG
from kraft.constants import DEFCONFIG
from kraft.constants import MAKEFILE_UK
from kraft.constants import ENV_VAR_PATTERN
from kraft.constants import SPECIFCATION_LATEST
from kraft.constants import SUPPORTED_FILENAMES
from kraft.constants import KRAFTCONF_PREFERRED_ARCHITECTURE
from kraft.constants import KRAFTCONF_PREFERRED_PLATFORM

from kraft.config.kconfig import infer_arch_config_name
from kraft.config.kconfig import infer_plat_config_name
from kraft.config.kconfig import infer_lib_config_name

from kraft.config.serialize import serialize_config

class Project(object):
    _name = None
    _path = None

    _core = None
    _config = {}
    _architectures = {}
    _platforms = {}
    _libraries = {}
    _volumes = {}
    _networks = {}

    def __init__(self,
        name,
        core=None,
        path=None,
        config=None,
        architectures=None,
        platforms=None,
        libraries=None,
        volumes=None,
        networks=None):
        
        self._name = name
        self._path = path
        self._core = core or Core()
        self._config = config or {
            'specification': SPECIFCATION_LATEST
        }
        self._architectures = architectures or Architectures([])
        self._platforms = platforms or Platforms([])
        self._libraries = libraries or Libraries([])
        self._volumes = volumes or Volumes([])
        self._networks = networks or Networks([])
    
    @property
    def name(self):
        return self._name
    @property
    def path(self):
        return self._path
    @property
    def core(self):
        return self._core
    @property
    def config(self):
        return self._config
    @property
    def architectures(self):
        return self._architectures
    @property
    def platforms(self):
        return self._platforms
    @property
    def libraries(self):
        return self._libraries
    @property
    def volumes(self):
        return self._volumes
    @property
    def networks(self):
        return self._networks

    @classmethod
    @kraft_context
    def from_config(ctx, cls, path, config, name_override=None):
        """Construct a Unikraft application from a config.Config object."""

        if name_override:
            config.name = name_override
    
        try:
            core = Core.from_config(config.unikraft)
            logger.debug("Discovered %s" % core)

            architectures = Architectures([])
            for arch in config.architectures:
                architecture = Architecture.from_config(core, arch, config.architectures[arch])
                logger.debug("Discovered %s" % architecture)
                architectures.add(arch,  architecture, config.architectures[arch])

            platforms = Platforms([])
            for plat in config.platforms:
                platform = Platform.from_config(core, plat, config.platforms[plat])
                logger.debug("Discovered %s" % platform)
                platforms.add(plat, platform, config.platforms[plat])

            libraries = Libraries([])
            for lib in config.libraries:
                library = Library.from_config(lib, config.libraries[lib])
                logger.debug("Discovered %s" % library)
                libraries.add(lib, library, config.libraries[lib])

            volumes = Volumes.from_config(ctx.workdir, config.volumes)
            networks = Networks.from_config(config.networks)

        except InvalidRepositorySource as e:
            logger.fatal(e)

        project = cls(
            name = config.name,
            core = core,
            path = path,
            config = config,
            architectures = architectures,
            platforms = platforms,
            libraries = libraries,
            volumes = volumes,
            networks = networks
        )

        return project

    def gen_make_cmd(self, extra=None, verbose=False):
        """Return a string with a correctly formatted make entrypoint for this
        application"""

        cmd = [
            'make',
            '-C', self.core.localdir,
            ('A=%s' % self.path)
        ]
        paths = []

        if verbose:
            cmd.append('V=1')

        for lib in self.libraries.all():
            paths.append(lib.repository.localdir)

        cmd.append('L=%s' % ":".join(paths))

        if type(extra) is list:
            for i in extra:
                cmd.append(i)

        elif type(extra) is str:
            cmd.append(extra)

        return cmd
    
    @kraft_context
    def make(ctx, self, extra=None):
        """Run a make target for this project."""
        self.checkout()
        cmd = self.gen_make_cmd(extra, ctx.verbose)
        util.execute(cmd)

    @kraft_context
    def configure(ctx, self, target_arch=None, target_plat=None):
        """Configure a Unikraft application."""

        if not self.is_configured():
            self.init()

        self.checkout()

        # Generate a dynamic .config to populate defconfig with based on
        # configure's parameterization.
        dotconfig = []
        
        if 'kconfig' in self.config.unikraft:
            dotconfig.extend(self.config.unikraft['kconfig'])
        
        found_arch = False
        for arch in self.architectures.all():
            if target_arch == arch.name:
                found_arch = True
                logger.info("Using %s" % arch.repository)
                kconfig_enable = arch.repository.kconfig_enabled_flag()
                if kconfig_enable:
                    dotconfig.extend([kconfig_enable])
                if isinstance(arch.config, (dict)) and 'kconfig' in arch.config:
                    dotconfig.extend(arch.config['kconfig'])
                dotconfig.extend(arch.repository.kconfig_extra)
        
        if not found_arch:
            raise MismatchTargetArchitecture(target_arch, [arch.name for arch in self.architectures.all()])
        
        found_plat = False
        for plat in self.platforms.all():
            if target_plat == plat.name:
                found_plat = True
                logger.info("Using %s" % plat.repository)
                kconfig_enable = plat.repository.kconfig_enabled_flag()
                if kconfig_enable:
                    dotconfig.extend([kconfig_enable])
                if isinstance(plat.config, (dict)) and 'kconfig' in plat.config:
                    dotconfig.extend(plat.config['kconfig'])
                dotconfig.extend(plat.repository.kconfig_extra)

        if not found_plat:
            raise MismatchTargetPlatform(target_plat, [plat.name for plat in self.platforms.all()])
            
        for lib in self.libraries.all():
            logger.info("Using %s" % lib.repository)
            kconfig_enable = lib.repository.kconfig_enabled_flag()
            if kconfig_enable:
                dotconfig.extend([kconfig_enable])
            if isinstance(lib.config, (dict)) and 'kconfig' in lib.config:
                dotconfig.extend(lib.config['kconfig'])
            dotconfig.extend(lib.repository.kconfig_extra)

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

    def menuconfig(self):
        """Run the make menuconfig target"""
        self.checkout()
        cmd = self.gen_make_cmd('menuconfig')
        logger.debug("Running: %s" % ' '.join(cmd))
        subprocess.run(cmd)

    def kmenuconfig(self):
        """Run the make kmenuconfig target"""
        self.checkout()
        cmd = self.gen_make_cmd('kmenuconfig')
        logger.debug("Running: %s" % ' '.join(cmd))
        subprocess.run(cmd)

    def init(self, force_create=False):
        """Initialize a repository"""
        makefile_uk = os.path.join(self.path, MAKEFILE_UK)
        if os.path.exists(makefile_uk) is False or force_create:
            Path(makefile_uk).touch()
        
        kraft_yaml = os.path.join(self.path, SUPPORTED_FILENAMES[0])
        if os.path.exists(kraft_yaml) is False or force_create:
            with open(kraft_yaml, 'w+') as file:
                file.write(self.toYAML())

    def is_configured(self):
        if os.path.exists(os.path.join(self.path, DOT_CONFIG)) is False:
            return False

        if os.path.exists(os.path.join(self.path, MAKEFILE_UK)) is False:
            return False
        
        return True
    
    def build(self, n_proc=None):
        """Checkout all the correct versions based on the current app instance
        and run the build command."""

        extra = []
        if n_proc is not None:
            extra.append('-j%s' % str(n_proc))
            self.make('fetch')
            self.make('prepare')
        
        self.make(extra)

    def clean(self, proper=False):
        """Clean the application."""

        if proper:
            self.make("properclean")

        else:
            self.make("clean")
    
    def checkout(self):
        """Check out a particular version of the repository."""
        self.core.checkout()
        self.architectures.checkout()
        self.platforms.checkout()
        self.libraries.checkout()

    def __str__(self):
        text = " App name....... %s\n" % self.name \
             + " Core........... %s\n" % self.core \
             + " Libraries...... "
        for lib in self.libraries.all():
            text += "%s\n%17s" % (lib.repository, " ")
        return text

    @kraft_context
    def get_config(ctx, self):
        if 'specification' not in self.config:
            self.config['specification'] = SPECIFCATION_LATEST
    
        if 'source' not in self.config:
            dpath_util.new(self.config, 'unikraft/source', self.core.source)
        if 'version' not in self.config:
            dpath_util.new(self.config, 'unikraft/version', self.core.version)
            
        for arch in self.architectures.all():
            dpath_util.new(self.config, 'architectures/%s' % arch.name, True)

        for plat in self.platforms.all():
            dpath_util.new(self.config, 'platforms/%s' % plat.name, True)
            
        # for lib in self.libraries.all():
        #     print(lib)

        return self.config

    def toYAML(self):
        """Return a YAML with the serialized string of this object."""
        
        config = self.get_config()

        return serialize_config(config)