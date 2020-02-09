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
from pathlib import Path
from json.decoder import JSONDecodeError

import kraft.util as util
from kraft.logger import logger
from kraft.kraft import kraft_context

from kraft.component import Component
from kraft.components import Core
from kraft.components import Volume
from kraft.components import Volumes
from kraft.components import Library
from kraft.components import Libraries
from kraft.components import Platform
from kraft.components import Platforms
from kraft.components import Architecture
from kraft.components import Architectures
from kraft.components import Repository

from kraft.errors import CannotReadDepsJson
from kraft.errors import InvalidRepositorySource
from kraft.errors import MisconfiguredUnikraftProject

DEPS_JSON="deps.json"
DOT_CONFIG=".config"
DEFCONFIG="defconfig"
MAKEFILE_UK="Makefile.uk"
ENV_VAR_PATTERN=re.compile(r'([A-Z_^=]+)=(\'[/\w\.\-\s]+\')')

class Project(object):
    _name = None
    _path = None

    _core = None
    _core_config = None
    _architectures = {}
    _platforms = {}
    _libraries = {}
    # _volumes = {}
    # _networks = {}

    def __init__(self,
        name,
        core=None,
        path=None,
        core_config=None,
        architectures=None,
        platforms=None,
        libraries=None,
        volumes=None):
        
        self._name = name
        self._path = path
        self._core = core or Core()
        self._core_config = core_config or {}
        self._architectures = architectures or Architectures([])
        self._platforms = platforms or Platforms([])
        self._libraries = libraries or Libraries([])
        # self._volumes = volumes or Volumes({})
        # self._networks = networks or Networks({})
    
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
        return self._core_config
    @property
    def architectures(self):
        return self._architectures
    @property
    def platforms(self):
        return self._platforms
    @property
    def libraries(self):
        return self._libraries
    # @property
    # def volumes(self):
    #     return self._volumes
    # @property
    # def networks(self):
    #     return self._networks

    @classmethod
    @kraft_context
    def from_config(ctx, cls, path, config, name_override=None):
        """Construct a Unikraft application from a config.Config object."""

        if name_override:
            config.name = name_override
    
        try:
            core = Core.from_config(config.unikraft)
            logger.info("Using %s..." % core)

            architectures = Architectures([])
            for arch in config.architectures:
                architecture = Architecture.from_config(core, arch, config.architectures[arch])
                logger.info("Using %s via %s..." % (arch, architecture))
                architectures.add(arch,  architecture, config.architectures[arch])

            platforms = Platforms([])
            for plat in config.platforms:
                platform = Platform.from_config(core, plat, config.platforms[plat])
                logger.info("Using %s via %s..." % (plat, platform))
                platforms.add(plat, platform, config.platforms[plat])

            libraries = Libraries([])
            for lib in config.libraries:
                library = Library.from_config(lib, config.libraries[lib])
                logger.info("Using %s..." % library)
                libraries.add(lib, library, config.libraries[lib])

            # volumes = Volumes({})
            # for vol in config.volumes:
            #     print(vol)

            # networks = Networks({})
            # for net in config.networks:
            #     print(net)

        except InvalidRepositorySource as e:
            logger.fatal(e)

        project = cls(
            name = config.name,
            core = core,
            path = path,
            core_config = config.unikraft,
            architectures = architectures,
            platforms = platforms,
            libraries = libraries,
        )

        return project
    
    def get_defconfig(self):
        dotconfig = []
        
        if 'kconfig' in self.config:
            dotconfig.extend(self.config['kconfig'])

        for arch in self.architectures.all():
            if 'kconfig' in arch.config:
                dotconfig.extend(arch.config['kconfig'])

        for plat in self.platforms.all():
            if 'kconfig' in plat.config:
                dotconfig.extend(plat.config['kconfig'])

        for lib in self.libraries.all():
            if 'kconfig' in lib.config:
                dotconfig.extend(lib.config['kconfig'])

        # Create a temporary file with the kconfig written to it
        fd, path = tempfile.mkstemp()

        with os.fdopen(fd, 'w+') as tmp:
            for line in dotconfig:
                tmp.write(line + '\n')

        return fd, path

    def gen_make_cmd(self, extra=None):
        """Return a string with a correctly formatted make entrypoint for this
        application"""

        cmd = [
            'make',
            '-C', self.core.localdir,
            ('A=%s' % self.path)
        ]
        paths = []

        for lib in self.libraries.all():
            paths.append(lib.repository.localdir)

        cmd.append('L=%s' % ":".join(paths))

        if type(extra) is list:
            for i in extra:
                cmd.append(i)

        elif type(extra) is str:
            cmd.append(extra)

        return cmd
    
    def make(self, extra=None):
        """Run a make target for this project."""
        self.checkout()
        cmd = self.gen_make_cmd(extra)
        util.execute(cmd)

    def kconfig(self):
        env = self.dumpvarsconfig()

    def configure(self):
        """Configure a Unikraft application."""

        if not self.is_configured():
            self.init()

        fd, path = self.get_defconfig()
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

    def init(self):
        """Initialize a repository"""
        makefile_uk = os.path.join(self.path, MAKEFILE_UK)
        if os.path.exists(makefile_uk) is False:
            Path(makefile_uk).touch()

    def is_configured(self):
        if os.path.exists(os.path.join(self.path, DOT_CONFIG)) is False:
            return False

        if os.path.exists(os.path.join(self.path, MAKEFILE_UK)) is False:
            return False
    
    def build(self, n_proc=None):
        """Checkout all the correct versions based on the current app instance
        and run the build command."""

        extra = []
        if n_proc is not None:
            extra.append('-j%s' % str(n_proc))
        
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
            text += "%s\n%17s" % (lib[1], " ")
        return text

    def toYAML(self):
        """Return a YAML with the serialized string of this object."""
        pass
