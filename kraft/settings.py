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

import os
from pathlib import Path

import dpath.util
import toml
from toml import TomlEncoder

from kraft.logger import logger


class TomlArraySeparatorEncoder(TomlEncoder):
    def __init__(self, _dict=dict, preserve=False, separator=",\n"):
        super(TomlArraySeparatorEncoder, self).__init__(_dict, preserve)
        if separator.strip() == "":
            separator = "," + separator
        elif separator.strip(' \t\n\r,'):
            raise ValueError("Invalid separator for arrays")
        self.separator = separator

    def dump_list(self, v):
        t = []
        retval = "[\n"
        for u in v:
            t.append(self.dump_value(u))
        while t != []:
            s = []
            for u in t:
                if isinstance(u, list):
                    for r in u:
                        s.append(r)
                else:
                    retval += "  " + str(u) + self.separator
            t = s
        retval += "]"
        return retval


class Settings(object):
    _kraftconf = None
    _settings = {}

    def __init__(self, kraftconf):
        self._kraftconf = kraftconf

        if os.path.exists(kraftconf) is False:
            Path(kraftconf).touch()

        with open(self._kraftconf, 'r') as file:
            self._settings = toml.loads(file.read())

    def save(self):
        # Write everything from the the start of the file
        with open(self._kraftconf, 'w+') as file:
            file.write(toml.dumps(
                self._settings,
                encoder=TomlArraySeparatorEncoder()
            ))

    def get(self, prop, default=None):
        try:
            result = dpath.util.get(self._settings, prop)
        except KeyError:
            logger.debug('Missed setting lookup: %s', prop)
            result = default

        return result

    def set(self, prop, val=None):
        if val is not None:
            dpath.util.new(self._settings, prop, val)
            self.save()
