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

import click

from kraft.component import Component
from kraft.component import ComponentManager
from kraft.const import CONFIG_UK
from kraft.const import CONFIG_UK_ARCH
from kraft.const import KCONFIG
from kraft.const import KCONFIG_EQ
from kraft.const import KCONFIG_Y
from kraft.const import UK_CORE_ARCH_DIR
from kraft.error import DisabledComponentError
from kraft.logger import logger


class Architecture(Component):
    pass


class InternalArchitecture(Architecture):
    _core = None

    @property
    def core(self): return self._core

    def is_downloaded(self):
        if self._core is not None:
            return self._core.is_downloaded()
        logger.warn("Core has not been downloaded: Use: kraft list pull unikraft")
        return False

    _localdir = None

    @property
    @click.pass_context
    def localdir(ctx, self):
        if self._localdir is None and self._core is not None:
            arch_config = UK_CORE_ARCH_DIR % (self._core.localdir, CONFIG_UK)
            if not os.path.isfile(arch_config):
                logger.critical("Could not find: %s" % arch_config)
                return None

            with open(arch_config, 'r+') as f:
                data = f.read()
                matches = CONFIG_UK_ARCH.findall(data)

                for match in matches:
                    if match[2] == self._name:
                        path = match[1]
                        # python is dumb:
                        if path.startswith("/"):
                            path = path[1:]
                        self._localdir = os.path.join(self._core.localdir, path)
                        break

        return self._localdir

    @property
    def kconfig_enabled_flag(self):
        if self._kconfig_enabled_flag is None and self._core is not None:
            arch_config = UK_CORE_ARCH_DIR % (self._core.localdir, CONFIG_UK)
            if not os.path.isfile(arch_config):
                logger.critical("Could not find: %s" % arch_config)
                return None

            with open(arch_config, 'r+') as f:
                data = f.read()
                matches = CONFIG_UK_ARCH.findall(data)

                for match in matches:
                    if match[2] == self._name:
                        self._kconfig_enabled_flag = KCONFIG % KCONFIG_EQ % (
                            match[0], KCONFIG_Y
                        )
                        break

        return self._kconfig_enabled_flag

    @click.pass_context
    def __init__(ctx, self, *args, **kwargs):
        self._name = kwargs.get("name", None)
        self._core = kwargs.get("core", None)
        self._kconfig = list()

        config = kwargs.get("config", None)

        if isinstance(config, bool) and config is False:
            raise DisabledComponentError(self._name)

        if isinstance(config, dict):
            self._kconfig = config.get("kconfig", kwargs.get("kconfig", list()))


class ArchitectureManager(ComponentManager):
    pass
