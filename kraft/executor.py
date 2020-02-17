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

import platform
import subprocess

from kraft.logger import logger

QEMU_GUEST='qemu-guest'
XEN_GUEST='xen-guest'

class Executor(object):
    _base_cmd = ''
    _cmd = []

    def __init__(self, kernel=None, architecture=None, platform=None):
        self._cmd = ['-k', kernel]
        self._kernel = kernel
        self._architecture = architecture
        self._platform = platform
    
    def add_initrd(self, initrd=None):
        if initrd:
            self._cmd.extend(('-i', initrd))

    def add_virtio_nic(self, virtio_nic=None):
        if virtio_nic:
            self._cmd.extend(('-n', virtio_nic))

    def add_bridge(self, bridge=None):
        if bridge:
            self._cmd.extend(('-b', bridge))

    def add_interface(self, interface=None):
        if interface:
            self._cmd.extend(('-V', interface))

    def add_virtio_raw(self, image=None):
        if image:
            self._cmd.extend(('-d', image))

    def add_virtio_qcow2(self, image=None):
        if image:
            self._cmd.extend(('-q', image))

    def add_virtio_9pfs(self, image=None):
        if image:
            self._cmd.extend(('-e', image))

    def open_gdb(self, port=None):
        if port and isinstance(port, int):
            self._cmd.extend(('-g', port))

    def set_memory(self, memory=None):
        if memory and isinstance(memory, int):
            self._cmd.extend(('-m', memory))

    def set_cpu_sockets(self, cpu_sockets=None):
        if cpu_sockets and isinstance(cpu_sockets, int):
            self._cmd.extend(('-s', cpu_sockets))

    def set_cpu_cores(self, cpu_cores=None):
        if cpu_cores and isinstance(cpu_cores, int):
            self._cmd.extend(('-c', cpu_cores))

    def execute(self, extra_args=None, background=False, paused=False, dry_run=False):
        if background:
            self._cmd.append('-X')
        if paused:
            self._cmd.append('-P')
        if dry_run:
            self._cmd.append('-D')
        if extra_args:
            self._cmd.extend(('-a', ' '.join(extra_args)))

        # TODO: This sequence needs to be better throughout as a result of the 
        # provisioning of `plat-` repositories will have their own runtime
        # mechanics.  For now this is "hard-coded":
        if self._platform == 'xen':
            cmd = [XEN_GUEST]
            cmd.extend(self._cmd)
        elif self._platform == 'linuxu':
            cmd = [
                self._kernel
            ]
            if extra_args:
                cmd.extend(extra_args)
        else:
            if self._architecture == "x86_64":
                self._cmd.extend(('-t', 'x86pc'))
            elif self._architecture == "arm64":
                self._cmd.extend(('-t', 'arm64v'))
            
            if platform.machine() != self._architecture:
                self._cmd.append('-W')
            cmd = [QEMU_GUEST]
            cmd.extend(self._cmd)

        logger.debug('Running: %s' % ' '.join(cmd))
        subprocess.run(cmd)