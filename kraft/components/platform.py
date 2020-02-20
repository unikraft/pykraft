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
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITYs, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
from enum import Enum

from kraft.types import RepositoryType

from kraft.constants import UK_CORE_PLAT_DIR

from kraft.components.executor import Executor
from kraft.components.executor import ExecutorDriverEnum
from kraft.components.repository import Repository
from kraft.components.repository import RepositoryManager

class Platform(Repository):
    _executor = None
    
    @property
    def executor(self):
        return self._executor
    
    @executor.setter
    def executor(self, executor):
        self._executor = executor

    @classmethod
    def from_config(cls, core=None, plat=None, config=None, workdir=None, executor_base=None):
        if not core.is_downloaded:
            core.update()
    
        # Set the executor to the base in case we cannot later determine
        executor = executor_base
        executor_config = None
        platform = None
        
        if not isinstance(config, bool):
            if 'run' in config:
                executor_config = config['run']

            if 'source' in config:
                platform = super(Platform, cls).from_source_string(config['source'], RepositoryType.PLAT)
            
        if platform is None:
            platform = cls(
                name = plat,
                source = core.source,
                version = core.version,
                localdir = os.path.join(UK_CORE_PLAT_DIR % core.localdir, plat),
                repository_type = RepositoryType.PLAT
            )

        # Determine executor driver
        for driver_name, member in ExecutorDriverEnum.__members__.items():
            if member.name == plat:
                executor = member.cls.from_config(
                    config=executor_config,
                    workdir=workdir,
                    executor_base=executor_base
                )
                break

        platform.executor = executor
        return platform

    @classmethod
    def from_source_string(cls, name, source=None):
        return super(Platform, cls).from_source_string(
            name = name,
            source = source,
            repository_type = RepositoryType.PLAT
        )

class Platforms(RepositoryManager):
    pass