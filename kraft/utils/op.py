# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#          Gaulthier Gain <gaulthier.gain@uliege.be>
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
import shlex
import subprocess

from kraft.logger import logger

def execute_command(command, parameters=' '):
    """Run a specific command on the host."""
    subprocess.call(shlex.split(command + ' ' + ' '.join(parameters)))


def is_software_installed(program):
    """Check if a program/software is installed on the host."""
    rc = subprocess.call(['which', program], stdout=subprocess.DEVNULL)
    if rc == 0:
        return True
    return False

def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def execute(cmd="", env={}, dry_run=False):
    if type(cmd) is list:
        cmd = " ".join(cmd)

    logger.debug("Running: %s" % cmd)

    if not dry_run:
        cmd = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            env=merge_dicts(os.environ, env)
        )

        for line in cmd.stdout:
            logger.info(line.strip().decode('ascii'))
