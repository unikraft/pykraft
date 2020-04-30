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
from __future__ import absolute_import
from __future__ import unicode_literals

import os

from enum import Enum

from kraft.errors import InvalidVolumeDriver
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
    _source = None
    _driver = None
    _workdir = None

    def __init__(self, name=None, driver=None, source=None, workdir=None):
        self._name = name
        self._driver = driver
        self._source = source
        self._workdir = workdir

    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._source

    @property
    def driver(self):
        return self._driver[1]

    @property
    def workdir(self):
        return self._workdir

    @classmethod
    def from_config(cls, name, driver, config=None, workdir=None):
        source = None

        if 'source' in config:
            source = config['source']

            # Check if the path exists and simply warn the user for anything
            # not immediately retrievable
            if os.path.exists(source):
                pass
            elif workdir and os.path.exists(os.path.join(workdir, source)):
                source = os.path.join(workdir, source)
            else:
                logger.warn("The provide source path for '%s' could not be found: %s" % (name, source))

        if driver is None and 'driver' in config:
            driver = VolumeDriver.from_name(config['driver'])

        return cls(
            name=name,
            driver=driver,
            source=source,
            workdir=workdir
        )


class Volumes(object):
    _volumes = []

    def __init__(self, volume_base=[]):
        self._volumes = volume_base or []

    def add(self, volume):
        if isinstance(volume, Volume):
            # Remove existing volume with the same name so as to override
            for net in self._volumes:
                if net.name == volume.name:
                    self._volumes.remove(net)
                    break

            self._volumes.append(volume)

        elif isinstance(volume, Volumes):
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
    def from_config(cls, workdir=None, config=None):
        volumes = cls([])

        for vol in config:

            driver = None
            if 'driver' in config[vol]:
                driver = VolumeDriver.from_name(config[vol]['driver'])

            if driver:
                volumes.add(Volume.from_config(
                    name=vol,
                    driver=driver,
                    config=config[vol],
                    workdir=workdir,
                ))
            else:
                raise InvalidVolumeDriver(vol)

        return volumes
