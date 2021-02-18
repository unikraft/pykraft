# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <a.jung@lancs.ac.uk>
#
# Copyright (c) 2021, Lancaster University.  All rights reserved.
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

import six

from kraft.arch import Architecture
from kraft.arch import InternalArchitecture
from kraft.component import ComponentManager
from kraft.const import UK_CORE_ARCHS
from kraft.const import UK_CORE_PLATS
from kraft.plat import InternalPlatform
from kraft.plat import Platform


class Target(object):
    _core = None
    @property
    def core(self): return self._core

    _config = None
    @property
    def config(self): return self._config

    _name = None
    @property
    def name(self): return self._name

    _architecture = None
    @property
    def architecture(self): return self._architecture

    _platform = None
    @property
    def platform(self): return self._platform

    def __init__(self, *args, **kwargs):
        self._config = kwargs
        self._name = kwargs.get('name', None)
        self._core = kwargs.get('core', None)

        arch = kwargs.get('architecture', None)
        if isinstance(arch, Architecture):
            self._architecture = arch

        elif isinstance(arch, six.string_types):
            if arch in UK_CORE_ARCHS:
                self._architecture = InternalArchitecture(
                    name=arch,
                    core=self.core,
                )
            else:
                self._architecture = Architecture(
                    name=arch
                )

        plat = kwargs.get('platform', None)
        if isinstance(plat,  Platform):
            self._platform = plat

        elif isinstance(plat, six.string_types):
            if plat in UK_CORE_PLATS:
                self._platform = InternalPlatform(
                    name=plat,
                    core=self.core
                )
            else:
                self._platform = Platform(
                    name=plat
                )

    def repr(self):
        ret = {}

        if self.name is not None:
            ret['name'] = self.name
        if self.architecture is not None:
            ret['architecture'] = self.architecture.repr()
        if self.platform is not None:
            ret['platform'] = self.platform.repr()

        return ret


class TargetManager(ComponentManager):
    _core = None

    def __init__(self, components=[], core=None):
        super(TargetManager, self).__init__(
            components=components,
            cls=Target,
            core=core,
        )

        self._core = core

    def set(self, k, v):
        if k is not None:
            self._components[k] = v

    def repr(self):
        ret = []
        for k in self.all():
            ret.append(k.repr())
        return ret
