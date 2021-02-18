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

from enum import Enum

from kraft.logger import logger


class VolumeDriver(Enum):
    VOL_INITRD = ("initrd", [""])
    VOL_9PFS = ("9pfs", [
        "CONFIG_LIBDEVFS=y"
        "CONFIG_LIB9PFS=y"
    ])
    VOL_RAW = ("raw", [
        "CONFIG_LIBDEVFS=y"
    ])
    VOL_QCOW2 = ("qcow2", [
        "CONFIG_LIBDEVFS=y"
    ])

    @property
    def name(self):
        return self.value[0]

    @property
    def kconfig(self):
        return self.kconfig[0]

    @classmethod
    def from_name(cls, name=None):
        for vol in VolumeDriver.__members__.items():
            if name == vol[1].name:
                return vol

        return None


class Volume(object):
    _name = None

    @property
    def name(self): return self._name

    _source = None

    @property
    def source(self): return self._source

    _driver = None

    @property
    def driver(self): return self._driver

    _workdir = None

    @property
    def workdir(self): return self._workdir

    def __init__(self, *args, **kwargs):
        self._name = kwargs.get("name", None)
        self._driver = kwargs.get("driver", None)
        self._source = kwargs.get("source", None)
        self._workdir = kwargs.get("workdir", None)

    @classmethod
    def from_config(cls, name=None, config={}):
        return cls(
            name=name,
            driver=config.get('driver', None),
            source=config.get('source', None),
            workdir=config.get('workdir', None),
        )

    def repr(self):
        config = {}
        if self.driver is not None:
            config['driver'] = self.driver
        if self.source is not None:
            config['source'] = self.source

        return config


class VolumeManager(object):
    _volumes = []
    @property
    def volumes(self): return self._volumes

    def __init__(self, volume_base=[]):
        self._volumes = []

        if isinstance(volume_base, dict):
            for volume in volume_base.keys():
                self.add(Volume(
                    name=volume,
                    **volume_base[volume]
                ))

        elif isinstance(volume_base, list):
            for volume in volume_base:
                self.add(volume)

    def add(self, volume):
        if isinstance(volume, Volume):
            # Remove existing volume with the same name so as to override
            for vol in self._volumes:
                if vol.name == volume.name:
                    logger.warning('Overriding existing volume %s' % vol.name)
                    self._volumes.remove(vol)
                    break

            self._volumes.append(volume)

        elif isinstance(volume, VolumeManager):
            for vol in volume.all():
                self.add(vol)

    def get(self, key, default=None):
        for volume in self._volumes:
            if volume.name == key:
                return volume

        return default

    def all(self):
        return self._volumes

    @classmethod
    def from_config(cls, config=None):
        volumes = cls([])

        for vol in config:
            volumes.add(Volume.from_config(vol, config[vol]))

        return volumes

    def repr(self):
        config = {}

        for volume in self.all():
            config[volume.name] = volume.repr()

        return config
