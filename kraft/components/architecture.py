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
import re

from enum import Enum

from kraft.type import RepositoryType

from kraft.components.repository import Repository
from kraft.components.repository import RepositoryManager

from kraft.constants import UK_CONFIG_FILE
from kraft.constants import UK_CORE_ARCH_DIR
from kraft.constants import CONFIG_UK_ARCH
from kraft.constants import KCONFIG
from kraft.constants import KCONFIG_Y
    
class Architecture(Repository):
    @classmethod
    def from_config(cls, ctx, core=None, arch=None, config=None):
        assert ctx is not None, "ctx is undefined"

        arch_dir = UK_CONFIG_FILE % (UK_CORE_ARCH_DIR % core.localdir)
        
        if not os.path.isfile(arch_dir):
            core.checkout()

        known_archs = {}

        with open(arch_dir, 'r+') as f:
            data = f.read()
            matches = CONFIG_UK_ARCH.findall(data)

            for match in matches:
                known_archs[match[2]] = {
                    'kconfig': {
                        KCONFIG % match[0]: KCONFIG_Y
                    },
                    'localdir': core.localdir + match[1]
                }

        if arch in known_archs:
            return cls(
                name = arch,
                source = core.source,
                version = core.version,
                localdir = known_archs[arch]['localdir'],
                repository_type=RepositoryType.ARCH,
                kconfig_extra=known_archs[arch]['kconfig']
            )

        return None

    @classmethod
    def from_source_string(cls, name, source=None):
        return super(Architecture, cls).from_source_string(
            name = name,
            source = source, 
            repository_type = RepositoryType.ARCH
        )

class Architectures(RepositoryManager):
    pass