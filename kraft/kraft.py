# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Laboratories Europe GmbH., NEC Corporation.
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

import click

from kraft.cmd import cmd_build
from kraft.cmd import cmd_clean
from kraft.cmd import cmd_configure
from kraft.cmd import cmd_init
from kraft.cmd import cmd_list
from kraft.cmd import cmd_run
from kraft.cmd import cmd_up
from kraft.cmd import grp_lib
from kraft.context import KraftContext
from kraft.logger import logger
from kraft.util.cli import CONTEXT_SETTINGS
from kraft.util.cli import KraftHelpGroup


@click.option(
    '--verbose', '-v', 'verbose',
    help='Enables verbose mode.', is_flag=True
)
@click.option(
    '--yes', '-Y', 'assume_yes',
    help='Assume yes to any binary prompts.',
    is_flag=True
)
@click.option(
    '--timestamps', '-T', 'use_timestamps',
    help='Show timestamps in output logs.',
    is_flag=True
)
@click.option(
    '--no-color', '-C', 'no_color',
    help='Do not use colour in output logs.',
    is_flag=True
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
  env::KRAFTRC  The location of kraft's preferences file
             [default: ~/.kraftrc]

Help:
  For help using this tool, please open an issue on Github:
  https://github.com/unikraft/kraft
""")
@click.version_option()
@click.pass_context
def kraft(ctx, verbose=False, assume_yes=False, use_timestamps=False,
          no_color=False):
    logger.use_timestamps = use_timestamps
    logger.use_color = not no_color

    ctx.obj = KraftContext(
        verbose=verbose,
        assume_yes=assume_yes
    )

    ctx.obj.cache.sync()


kraft.add_command(cmd_list)
kraft.add_command(cmd_up)
kraft.add_command(cmd_init)
kraft.add_command(cmd_configure)
kraft.add_command(cmd_build)
kraft.add_command(cmd_run)
kraft.add_command(cmd_clean)
kraft.add_command(grp_lib)
