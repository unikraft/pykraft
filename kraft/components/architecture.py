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
import sys

from kraft.component import Component
from kraft.components.repository import Repository
from kraft.components.repository import RepositoryManager

UK_CONFIG_FILE='%s/Config.uk'
UK_CORE_ARCH_DIR='%s/arch'
CONFIG_UK_ARCH=re.compile(r'source "\$\(UK_BASE\)(\/arch\/[\w_]+\/(\w+)\/)Config\.uk"$')

class Architecture(Repository):
    @classmethod
    def from_config(cls, core=None, arch=None, config=None):
        arch_dir = UK_CONFIG_FILE % (UK_CORE_ARCH_DIR % core.localdir)
        if not os.path.isfile(arch_dir):
            core.checkout()

        with open(arch_dir) as f:
            for line in f:
                match = CONFIG_UK_ARCH.findall(line)
                if len(match) > 0:
                    path, found_arch = match[0]
                    if found_arch == arch:
                        # TODO: os.path.join(core.localdir, path) isn't working for me?
                        return cls(
                            name = arch,
                            source = core.source,
                            version = core.version,
                            localdir = core.localdir + path,
                            component_type=Component.ARCH
                        )

        return None

    @classmethod
    def from_source_string(cls, name, source=None):
        return super(Architecture, cls).from_source_string(
            name = name,
            source = source, 
            component_type = Component.ARCH
        )

class Architectures(RepositoryManager):
    pass