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

import logging

import click

from kraft import __program__

TIME_FORMAT = "%(asctime)s "
LEVEL_FORMAT = "%(levelname)-8s"
MESSAGE_FORMAT = "%(message)s"
LOGGING_COLORS = {
    'WARNING':  'yellow',
    'INFO':     'white',
    'DEBUG':    'cyan',
    'CRITICAL': 'red',
    'ERROR':    'red'
}


class KraftFormatter(logging.Formatter):
    _use_color = False
    _logger = None

    def __init__(self, *args, **kwargs):
        self._logger = kwargs.get("logger")
        if self._logger is not None:
            del kwargs["logger"]

        logging.Formatter.__init__(self, *args, **kwargs)

    def format(self, record):
        fmt = ""

        if self._logger.use_timestamps:
            fmt += TIME_FORMAT

        fmt += "["
        if self._logger.use_color:
            fmt += click.style(LEVEL_FORMAT, fg=LOGGING_COLORS[record.levelname])
        else:
            fmt += LEVEL_FORMAT
        fmt += "] "

        fmt += MESSAGE_FORMAT

        self._style._fmt = fmt

        return logging.Formatter.format(self, record)


class KraftLogger(logging.Logger):
    _use_timestamps = False
    @property
    def use_timestamps(self): return self._use_timestamps

    @use_timestamps.setter
    def use_timestamps(self, use_timestamps=False):
        self._use_timestamps = use_timestamps

    _use_color = True
    @property
    def use_color(self): return self._use_color

    @use_color.setter
    def use_color(self, use_color=False):
        self._use_color = use_color

    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.ERROR)

        color_formatter = KraftFormatter(
            logger=self,
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)


logging.setLoggerClass(KraftLogger)
logger = logging.getLogger(__program__)
