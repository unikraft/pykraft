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
from __future__ import absolute_import
from __future__ import unicode_literals

import click

from kraft.commands import build
from kraft.commands import clean
from kraft.commands import configure
from kraft.commands import develdependency
from kraft.commands import init
from kraft.commands import libbump
from kraft.commands import libinit
from kraft.commands import list
from kraft.commands import run
from kraft.commands import up
from kraft.context import kraft_context
from kraft.utils.cli import CONTEXT_SETTINGS
from kraft.utils.cli import KraftHelpGroup


@click.option('--verbose',                    '-v', 'verbose',                help='Enables verbose mode.', is_flag=True)  # noqa: E501,E261
@click.option('--no-checkout',                '-X', 'dont_checkout',          help='Toggle checking-out repositories before any action.', is_flag=True)  # noqa: E501,E261
@click.option('--ignore-git-checkout-errors', '-C', 'ignore_checkout_errors', help='Ignore checkout errors.', is_flag=True)  # noqa: E501,E261
@click.option('--assume-yes',                 '-Y', 'assume_yes',             help='Assume yes to any binary prompts.', is_flag=True)  # noqa: E501,E261
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
def kraft(ctx, verbose, dont_checkout, ignore_checkout_errors, assume_yes):
    ctx.verbose = verbose
    ctx.dont_checkout = dont_checkout
    ctx.ignore_checkout_errors = ignore_checkout_errors
    ctx.assume_yes = assume_yes
    ctx.cache.sync()


@click.group(name='lib', short_help='Unikraft library commands.')
@kraft_context
def lib(ctx):
    """
    Unikraft library sub-commands are useful for maintaining and working
    directly with Unikraft libraries.
    """
    pass

@click.group(name='devel', short_help='Unikraft devel commands.')
@kraft_context
def devel(ctx):
    """
    Unikraft developer sub-commands useful for maintaing and working
    directly with Unikraft source code.
    """
    pass

lib.add_command(libinit)
lib.add_command(libbump)
devel.add_command(develdependency)

kraft.add_command(up)
kraft.add_command(run)
kraft.add_command(init)
kraft.add_command(list)
kraft.add_command(build)
kraft.add_command(clean)
kraft.add_command(configure)
kraft.add_command(lib)
kraft.add_command(devel)