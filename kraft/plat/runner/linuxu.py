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

import subprocess

import kraft.util as util
from .runner import Runner
from kraft.logger import logger


class LinuxuRunner(Runner):
    _base_cmd = ''

    def add_initrd(self, initrd=None):
        pass

    def add_virtio_nic(self, virtio_nic=None):
        pass

    def add_bridge(self, bridge=None):
        pass

    def add_interface(self, interface=None):
        pass

    def add_virtio_raw(self, image=None):
        pass

    def add_virtio_qcow2(self, image=None):
        pass

    def add_virtio_9pfs(self, image=None):
        pass

    def open_gdb(self, port=None):
        pass

    def set_memory(self, memory=None):
        pass

    # TODO: Pin CPUs with isolcpus or taskset
    def set_cpu_sockets(self, cpu_sockets=None):
        pass

    # TODO: Pin CPUs with isolcpus or taskset
    def set_cpu_cores(self, cpu_cores=None):
        pass

    def execute(self, extra_args=None, background=False, paused=False,
                dry_run=False):
        logger.debug("Executing on Linux...")

        cmd = [
            self.unikernel
        ]

        if self.arguments:
            cmd.append(self.arguments)

        if extra_args:
            cmd.extend(extra_args)

        for pre_up_cmd in self._pre_up:
            util.execute(pre_up_cmd, dry_run=dry_run)

        cmd = list(map(str, cmd))
        logger.debug('Running: %s' % ' '.join(cmd))

        if not dry_run:
            process = subprocess.Popen(cmd)

            try:
                process.wait()

            except KeyboardInterrupt:
                try:
                    process.terminate()
                except OSError:
                    pass
                process.wait()

        for post_down_cmd in self._post_down:
            util.execute(post_down_cmd, dry_run=dry_run)
