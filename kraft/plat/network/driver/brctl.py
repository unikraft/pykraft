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
from shutil import which

import kraft.util as util
from .driver import NetworkDriver
from kraft.error import InvalidBridgeName
from kraft.error import NetworkBridgeUnsupported
from kraft.logger import logger

BRCTL = "brctl"


class BRCTLDriver(NetworkDriver):
    def __init__(self, name, type):
        super(BRCTLDriver, self).__init__(name, type)

    def integrity_ok(self):
        return which(BRCTL) is not None

    def create_bridge(self, name=None, dry_run=False):
        if not self.integrity_ok():
            raise NetworkBridgeUnsupported(self.type.name)

        if name is None:
            name = self._name

        if self.bridge_exists(name):
            logger.warning("Bridge '%s' already exists!" % name)
            return True

        if name is not None and len(name) > 0:
            util.execute([
                BRCTL, "addbr", name
            ], dry_run=dry_run)
        else:
            raise InvalidBridgeName(name)

        return True

    def destroy_bridge(self, name=None):
        if not self.integrity_ok():
            raise NetworkBridgeUnsupported(self.type.name)

        if name is None:
            name = self.name

        if name is not None and len(name) > 0:
            util.execute([
                BRCTL, "delbr", name
            ])
        else:
            raise InvalidBridgeName(name)

    def bridge_exists(self, name=None):
        if not self.integrity_ok():
            raise NetworkBridgeUnsupported(self.type.name)

        process = subprocess.Popen(
            [BRCTL, "show", name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = process.communicate()

        if err == b"can't get info No such device\n":
            return False
        elif "does not exist!" in err.decode('utf-8'):
            return False

        return True
