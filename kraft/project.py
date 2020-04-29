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

import kraft.utils as utils
from kraft.logger import logger
from kraft.kraft import kraft_context
from kraft.components.types import RepositoryType

from kraft.components.core import Core
from kraft.components.library import Library
from kraft.components.library import Libraries
from kraft.components.platform import Platform
from kraft.components.platform import Platforms
from kraft.components.executor import Executor
from kraft.components.architecture import Architecture
from kraft.components.architecture import Architectures
from kraft.components.repository import Repository

from kraft.errors import CannotReadKraftfile
from kraft.errors import InvalidRepositorySource
from kraft.errors import MisconfiguredUnikraftProject
from kraft.errors import MismatchTargetArchitecture
from kraft.errors import MismatchTargetPlatform
from kraft.errors import KraftFileNotFound

from kraft.constants import UNIKRAFT_CORE
from kraft.constants import KCONFIG_Y
from kraft.constants import DOT_CONFIG
from kraft.constants import DEFCONFIG
from kraft.constants import MAKEFILE_UK
from kraft.constants import ENV_VAR_PATTERN
from kraft.constants import KRAFT_SPEC_LATEST
from kraft.constants import SUPPORTED_FILENAMES
from kraft.constants import KRAFTCONF_CONFIGURE_PLATFORM
from kraft.constants import KRAFTCONF_CONFIGURE_ARCHITECTURE

from kraft.config.config import get_default_config_files
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

    def __init__(self,
        name,
        core=None,
        path=None,
        config=None,
        architectures=None,
        platforms=None,
        libraries=None):
        
        self._name = name
        self._path = path
        self._core = core or Core()
        self._config = config or {
            'specification': KRAFT_SPEC_LATEST
        }
        self._architectures = architectures or Architectures([])
        self._platforms = platforms or Platforms([])
        self._libraries = libraries or Libraries([])
    
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

    @classmethod
    @kraft_context
    def from_config(ctx, cls, path, config, name_override=None):
        """Construct a Unikraft application from a config.Config object."""

        if name_override:
            config.name = name_override
    
        try:
            core = Core.from_config(ctx, config.unikraft)
            executor_base = Executor.from_config(ctx, config.executor)
            logger.debug("Discovered %s" % core)

            architectures = Architectures([])
            for arch in config.architectures:
                architecture = Architecture.from_config(ctx, core, arch, config.architectures[arch])
                logger.debug("Discovered %s" % architecture)
                architectures.add(arch,  architecture, config.architectures[arch])

            platforms = Platforms([])
            for plat in config.platforms:
                platform = Platform.from_config(ctx, core, plat, config.platforms[plat], executor_base)
                logger.debug("Discovered %s" % platform)
                platforms.add(plat, platform, config.platforms[plat])

            libraries = Libraries([])
            for lib in config.libraries:
                library = Library.from_config(ctx, lib, config.libraries[lib])
                logger.debug("Discovered %s" % library)
                libraries.add(lib, library, config.libraries[lib])

        except InvalidRepositorySource as e:
            logger.fatal(e)

        project = cls(
            name = config.name,
            core = core,
            path = path,
            config = config,
            architectures = architectures,
            platforms = platforms,
            libraries = libraries
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

        if verbose:
            cmd.append('V=1')
        
        plat_paths = []
        for plat in self.platforms.all():
            if plat.repository.source != UNIKRAFT_CORE:
                plat_paths.append(plat.repository.localdir)
        
        cmd.append('P=%s' % ":".join(plat_paths))
        
        lib_paths = []
        for lib in self.libraries.all():
            lib_paths.append(lib.repository.localdir)

        cmd.append('L=%s' % ":".join(lib_paths))

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
        utils.execute(cmd)

    @kraft_context
    def configure(ctx, self, target_arch=None, target_plat=None, force_configure=False):
        """Configure a Unikraft application."""

        if not self.is_configured():
            self.init()

        self.checkout()

        if force_configure:
            # Check if we have used "--arch" before.  This saves the user from having to
            # re-type it.  This means omission uses the settings.
            if target_arch is None and len(self.architectures.all()) > 1 and ctx.settings.get(KRAFTCONF_CONFIGURE_ARCHITECTURE):
                target_arch = ctx.settings.get(KRAFTCONF_CONFIGURE_ARCHITECTURE)
            
            elif target_arch is None and len(self.architectures.all()) == 1:
                for arch in self.architectures.all():
                    target_arch = arch.name

            if target_arch is not None and ctx.settings.get(KRAFTCONF_CONFIGURE_ARCHITECTURE) is None:
                ctx.settings.set(KRAFTCONF_CONFIGURE_ARCHITECTURE, target_arch)

            # Check if we have used "--plat" before.  This saves the user from having to
            # re-type it.  This means omission uses the settings.
            if target_plat is None and len(self.platforms.all()) > 1 and ctx.settings.get(KRAFTCONF_CONFIGURE_PLATFORM):
                target_plat = ctx.settings.get(KRAFTCONF_CONFIGURE_PLATFORM)
            
            elif target_plat is None and len(self.platforms.all()) == 1:
                for plat in self.platforms.all():
                    target_plat = plat.name
            
            if target_plat is not None and ctx.settings.get(KRAFTCONF_CONFIGURE_PLATFORM) is None:
                ctx.settings.set(KRAFTCONF_CONFIGURE_PLATFORM, target_plat)

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
    
        try:
            filenames = get_default_config_files(self.path)
        except KraftFileNotFound:
            filenames = []

        if len(filenames) == 0 or force_create:
            kraft_yaml = os.path.join(self.path, SUPPORTED_FILENAMES[0])
            with open(kraft_yaml, 'w+') as file:
                file.write(self.to_yaml())

    def is_configured(self):
        if os.path.exists(os.path.join(self.path, DOT_CONFIG)) is False:
            return False

        if os.path.exists(os.path.join(self.path, MAKEFILE_UK)) is False:
            return False
        
        return True
    
    def build(self, fetch=True, prepare=True, target=None, n_proc=None):
        """Checkout all the correct versions based on the current app instance
        and run the build command."""

        extra = []
        if n_proc is not None:
            extra.append('-j%s' % str(n_proc))
        
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

    def to_yaml(self):
        """Return a YAML with the serialized string of this object."""
        
        config = self.get_config()

        return serialize_config(config)