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
from kraft.utils.cli import KraftHelpGroup
from kraft.utils.cli import CONTEXT_SETTINGS

from kraft.commands import (
    up,
    run,
    init,
    list,
    build,
    clean,
    initlib,
    configure,
)

@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='Enables verbose mode.'
)
@click.option(
    '-X', '--dont-checkout', 'dont_checkout',
    is_flag=True,
    help='Do not checkout repositories.'
)
@click.option(
    '-C', '--ignore-git-checkout-errors', 'ignore_checkout_errors',
    is_flag=True,
    help='Ignore checkout errors.'
)
@click.group(cls=KraftHelpGroup, context_settings=CONTEXT_SETTINGS, epilog="""
Influential Environmental Variables:
  env::UK_WORKDIR The working directory for all Unikraft
             source code [default: ~/.unikraft]
  env::UK_ROOT    The directory for Unikraft's core source
             code [default: $UK_WORKDIR/unikraft]
  env::UK_LIBS    The directory of all the external Unikraft
             libraries [default: $UK_WORKDIR/libs]
  env::UK_APPS    The directory of all the template applications
             [default: $UK_WORKDIR/apps]
  env::KRAFTCONF  The location of kraft's preferences file
             [default: ~/.kraftrc]

Help:
  For help using this tool, please open an issue on Github:
  https://github.com/unikraft/kraft
""")
@click.version_option()
@kraft_context
def kraft(ctx, verbose, dont_checkout, ignore_checkout_errors):
    ctx.verbose = verbose
    ctx.dont_checkout = dont_checkout
    ctx.ignore_checkout_errors = ignore_checkout_errors
    ctx.cache.sync()

@click.group(name='devel', short_help='Unikraft developer commands.')
@kraft_context
def devel(ctx):
    """Unikraft developer sub-commands useful for maintaing and working
    directly with Unikraft source code."""
    pass

@click.group(name='measure', short_help='Unikraft measurement commands.')
@kraft_context
def measure(ctx):
    """Unikraft measurement commands are ..."""
    pass

devel.add_command(initlib)

kraft.add_command(up)
kraft.add_command(run)
kraft.add_command(init)
kraft.add_command(list)
kraft.add_command(build)
kraft.add_command(clean)
kraft.add_command(configure)
kraft.add_command(devel)
