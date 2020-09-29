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

import click

from kraft.error import DisabledComponentError

from kraft.const import UK_CORE_PLAT_DIR

from kraft.component import Component
from kraft.component import ComponentManager

from .runner import RunnerTypes


class Platform(Component):
    _runner = None
    @property
    def runner(self): return self._runner

    @click.pass_context
    def __init__(ctx, self, *args, **kwargs):
        self._name = kwargs.get("name", None)
        self._runner = kwargs.get("runner", None)

        if self._runner is None:
            for r in RunnerTypes.__members__.values():
                if self._name == r.name:
                    self._runner = r.cls
                    break


class InternalPlatform(Platform):
    _core = None
    @property
    def core(self): return self._core

    def is_downloaded(self):
        if self._core is not None:
            return self._core.is_downloaded()
        return False

    _localdir = None
    @property
    @click.pass_context
    def localdir(ctx, self):
        if self._localdir is None and self._core is not None:
            self._localdir = UK_CORE_PLAT_DIR % (
                self._core.localdir, self._name
            )

        return self._localdir

    @click.pass_context
    def __init__(ctx, self, *args, **kwargs):
        super(InternalPlatform, self).__init__(*args, **kwargs)

        self._core = kwargs.get("core", None)
        self._kconfig = list()

        config = kwargs.get("config", None)

        if isinstance(config, bool) and config is False:
            raise DisabledComponentError(self._name)

        if isinstance(config, dict):
            version = config.get("version", None)
            self._kconfig = config.get("kconfig", kwargs.get("kconfig", list()))


class PlatformManager(ComponentManager):
    pass
