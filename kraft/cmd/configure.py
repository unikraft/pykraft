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
import sys

import click

from kraft.app import Application
from kraft.cmd.list import kraft_list_preflight
from kraft.const import KCONFIG
from kraft.const import KCONFIG_EQ
from kraft.const import KCONFIG_N
from kraft.const import KCONFIG_Y
from kraft.error import CannotConfigureApplication
from kraft.error import KraftError
from kraft.logger import logger


@click.command('configure', short_help='Configure the application.')  # noqa: C901
@click.option(
    '--plat', '-p', 'plat',
    help='Target platform.',
    metavar="PLAT"
)
@click.option(
    '--arch', '-m', 'arch',
    help='Target architecture.',
    metavar="ARCH"
)
@click.option(
    '--force', '-F', 'force_configure',
    help='Force writing new configuration.',
    is_flag=True
)
@click.option(
    '--menuconfig', '-k', 'show_menuconfig',
    help='Use Unikraft\'s ncurses Kconfig editor.',
    is_flag=True
)
@click.option(
    '--workdir', '-w', 'workdir',
    help='Specify an alternative directory for the application [default is cwd].',
    metavar="PATH"
)
@click.option(
    '--yes', '-y', 'yes',
    multiple=True,
    help='Specify an option to enable.'
)
@click.option(
    '--no', '-n', 'no',
    multiple=True,
    help='Specify an option to disable.'
)
@click.option(
    '--set', '-s', 'opts',
    multiple=True,
    help='Set an option\'s value.'
)
@click.pass_context
def cmd_configure(ctx, plat=None, arch=None, force_configure=False,
                  show_menuconfig=False, workdir=None, yes=[], no=[], opts=[]):
    """
    Configure the unikernel using the KConfig options set in the kraft.yaml
    file.  Alternatively, you can use the -k|--menuconfig flag to open the TUI
    to manually select the configuration for this unikernel.

    When the unikernel is configured, a .config file is written to the working
    directory with the selected KConfig options.
    """

    kraft_list_preflight()

    if workdir is None:
        workdir = os.getcwd()

    options = list()
    for y in yes:
        if not y.startswith(KCONFIG):
            y = KCONFIG % y
        options.append(KCONFIG_EQ % (y, KCONFIG_Y))
    for n in no:
        if not n.startswith(KCONFIG):
            n = KCONFIG % n
        if n in options:
            logger.critical('Cannot specify same option with multiple values: %s' % n)
            sys.exit(1)
        options.append(KCONFIG_EQ % (n, KCONFIG_N))
    for o in opts:
        if not o.startswith(KCONFIG):
            o = KCONFIG % o
        if '=' not in o:
            logger.critical('Missing value for --set option: %s' % o)
            sys.exit(1)
        options.append(o)

    try:
        kraft_configure(
            env=ctx.obj.env,
            workdir=workdir,
            plat=plat,
            arch=arch,
            force_configure=force_configure,
            show_menuconfig=show_menuconfig,
            options=options,
        )

    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)


@click.pass_context
def kraft_configure(ctx, env=None, workdir=None, plat=None, arch=None,
                    force_configure=False, show_menuconfig=False, options=[]):
    """
    Populates the local .config with the default values for the target
    application.
    """

    if workdir is None or os.path.exists(workdir) is False:
        raise ValueError("working directory is empty: %s" % workdir)

    logger.debug("Configuring %s..." % workdir)

    app = Application.from_workdir(workdir)
    if show_menuconfig:
        if sys.stdout.isatty():
            app.open_menuconfig()
            return
        else:
            raise KraftError("Cannot open menuconfig in non-TTY environment")

    if app.is_configured() and force_configure is False:
        if click.confirm("%s is already configured, would you like to overwrite configuration?" % workdir): # noqa
            force_configure = True
        else:
            raise CannotConfigureApplication(workdir)

    app.configure(
        arch=arch,
        plat=plat,
        options=options,
    )
