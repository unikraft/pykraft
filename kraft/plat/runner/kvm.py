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

from kraft.logger import logger

from kraft.const import QEMU_GUEST

import kraft.util as util

from .runner import Runner


class KVMRunner(Runner):
    def execute(self,  # noqa: C901
                extra_args=None,
                background=False,
                paused=False,
                dry_run=False):
        logger.debug("Executing on KVM...")

        self._cmd.extend(('-k', self.unikernel))

        if background:
            self._cmd.append('-x')
        if paused:
            self._cmd.append('-P')
        if dry_run:
            self._cmd.append('-D')
        if extra_args:
            self._cmd.extend(('-a', ' '.join(extra_args)))

        self.automount(dry_run)
        self.autoconnect(dry_run)

        if self.architecture == "x86_64":
            self._cmd.extend(('-t', 'x86pc'))
        elif self.architecture == "arm64":
            self._cmd.extend(('-t', 'arm64v'))

        # if platform.machine() != self.architecture:
        #     self._cmd.append('-W')

        if self.arguments:
            self._cmd.extend(('-a', self.arguments))

        cmd = [QEMU_GUEST]

        cmd.extend(self._cmd)

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
