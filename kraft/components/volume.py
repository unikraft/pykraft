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

import os
from enum import Enum

from kraft.logger import logger
from kraft.errors import InvalidVolumeType

class VolumeType(Enum):
    VOL_INITRD = ( "initrd"  , [""] )
    VOL_9PFS   = ( "9pfs"    , [
        "CONFIG_LIBDEVFS=y"
        "CONFIG_LIB9PFS=y"
    ])
    VOL_RAW    = ( "raw"     , [
        "CONFIG_LIBDEVFS=y"
    ] )
    VOL_QCOW2  = ( "qcow2"   , [
        "CONFIG_LIBDEVFS=y"
    ] )

    @property
    def name(self):
        return self.value[0]

    @property
    def kconfig(self):
        return self.kconfig[0]
    
    @classmethod
    def from_name(cls, name = None):
        for vol in VolumeType.__members__.items():
            if name == vol[1].name:
                return vol
        
        return None

class Volume(object):
    _name = None
    _image = None
    _type = None

    def __init__(self, name=None, type=None, image=None):
        self._name = name
        self._type = type
        self._image = image

    @property
    def name(self):
        return self._name

    @property
    def image(self):
        return self._image

    @property
    def type(self):
        return self._type[1]
    
    @classmethod
    def from_config(cls, name, type, config=None, workdir=None):
        image = None

        if 'image' in config:
            image = config['image']

            # Check if the path exists and simply warn the user for anything
            # not immediately retrievable
            if os.path.exists(image):
                pass
            elif workdir and os.path.exists(os.path.join(workdir, image)):
                image = os.path.join(workdir, image)
            else:
                logger.warn("The provide image path for '%s' could not be found: %s" % (name, image))
        
        if type is None and 'type' in config:
            type = VolumeType.from_name(config['type'])

        return cls(
            name=name,
            type=type,
            image=image
        )
    
class Volumes(object):
    _volumes = []

    def __init__(self, volume_base=[]):
        self._volumes = volume_base or []

    def add(self, volume):
        self._volumes.append(volume)

    def get(self, key, default=None):
        for volume in self._volumes:
            if getattr(volume, key) == value:
                return volume

    def all(self):
        return self._volumes
    
    @classmethod
    def from_config(cls, workdir=None, config=None):
        volumes = cls([])

        for vol in config:

            vol_type = None
            if 'type' in config[vol]:
                vol_type = VolumeType.from_name(config[vol]['type'])

            if vol_type:
                volumes.add(Volume.from_config(
                    name=vol,
                    type=vol_type,
                    config=config[vol],
                    workdir=workdir,
                ))
            else:
                raise InvalidVolumeType(vol)
        
        return volumes