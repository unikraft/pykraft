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
#
# THIS HEADER MAY NOT BE EXTRACTED OR MODIFIED IN ANY WAY.

import os
import sys
import click
import logging
from .logger import logger
from .env import pass_environment
from kraft import __version__, __description__, __program__

CONTEXT_SETTINGS = dict(auto_envvar_prefix='UK')

cmd_folder = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'cmds')
)

class KraftCLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []

        for filename in os.listdir(cmd_folder):
            if filename.endswith('.py') and \
               filename.startswith('cmd_'):
                rv.append(filename[4:-3])

        rv.sort()

        return rv

    def get_command(self, ctx, name):
        try:
            if sys.version_info[0] == 2:
                name = name.encode('ascii', 'replace')
            mod = __import__('kraft.cmds.cmd_' + name,
                             None, None, ['cli'])
        except ImportError:
            return

        return mod.cli

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('kraft %s' % __version__)
    ctx.exit()

@click.command(
    cls=KraftCLI,
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='Enables verbose mode.'
)
@click.option(
    '-V', '--version',
    is_flag=True,
    help='Print the version and exit.',
    callback=print_version,
    expose_value=False,
    is_eager=True
)
@pass_environment
def cli(ctx, verbose):
    """
    {description}
    """.format(description = __description__)

    ctx.verbose = verbose

    if ctx.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
