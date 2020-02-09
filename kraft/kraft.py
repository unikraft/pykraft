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
import sys
import click
import logging

from kraft import __version__, __description__, __program__

from kraft.logger import logger
from kraft.config import config
from kraft.context import kraft_context

from kraft.commands.utils import CONTEXT_SETTINGS
from kraft.commands import (
    update,
    list,
    build,
    configure,
    run,
    clean
)

@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='Enables verbose mode.'
)
@click.option(
    '-w', '--workdir',
    type=click.Path(resolve_path=True),
    help='Use kraft on this working directory.',
)
@click.group(cls=click.Group, context_settings=CONTEXT_SETTINGS)
@click.version_option()
@kraft_context
def kraft(ctx, verbose, workdir):
    ctx.verbose = verbose

    if workdir:
        ctx.workdir = workdir
    
    ctx.cache.sync()

kraft.add_command(update)
kraft.add_command(list)
kraft.add_command(configure)
kraft.add_command(build)
kraft.add_command(clean)
kraft.add_command(run)
