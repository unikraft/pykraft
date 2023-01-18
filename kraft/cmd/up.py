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

import kraft.util as util
from kraft.cmd.build import kraft_build
from kraft.cmd.configure import kraft_configure
from kraft.cmd.init import kraft_app_init
from kraft.cmd.list import kraft_list_preflight
from kraft.cmd.list.pull import kraft_list_pull
from kraft.cmd.run import kraft_run
from kraft.const import KRAFTRC_CONFIGURE_ARCHITECTURE
from kraft.const import KRAFTRC_CONFIGURE_PLATFORM
from kraft.logger import logger


@click.command('up', short_help='Configure, build and run an application.')
@click.argument('name', required=True)
@click.option(
    '--workdir', '-w', 'workdir',
    help='Specify an alternative directory for the application [default is cwd].',
    metavar="PATH"
)
@click.option(
    '--template', '-t', 'template_app',
    help='Use an existing application as a template.',
    metavar="NAME",
    required=True
)
@click.option(
    '--plat', '-p', 'plat',
    help='Target platform.',
)
@click.option(
    '--arch', '-m', 'arch',
    help='Target architecture.',
)
@click.option(
    '--initrd', '-i', 'initrd',
    help='Provide an init ramdisk.'
)
@click.option(
    '--background', '-B', 'background',
    help='Run in background.',
    is_flag=True
)
@click.option(
    '--paused', '-P', 'paused',
    help='Run the application in paused state.',
    is_flag=True
)
@click.option(
    '--gdb', '-g', 'gdb',
    help='Run a GDB server for the guest on specified port.',
    type=int
)
@click.option(
    '--dbg', '-d', 'dbg',
    help='Use unstriped unikernel',
    is_flag=True
)
@click.option(
    '--virtio-nic', '-n', 'virtio_nic',
    help='Attach a NAT-ed virtio-NIC to the guest.'
)
@click.option(
    '--bridge', '-b', 'bridge',
    help='Attach a NAT-ed virtio-NIC an existing bridge.'
)
@click.option(
    '--interface', '-V', 'interface',
    help='Assign host device interface directly as virtio-NIC to the guest.'
)
@click.option(
    '--dry-run', '-D', 'dry_run',
    help='Perform a dry run.',
    is_flag=True
)
@click.option(
    '--memory', '-M', 'memory',
    help="Assign MB memory to the guest.",
    type=int
)
@click.option(
    '--cpu-sockets', '-s', 'cpu_sockets',
    help="Number of guest CPU sockets.",
    type=int
)
@click.option(
    '--cpu-cores', '-c', 'cpu_cores',
    help="Number of guest cores per socket.",
    type=int
)
@click.option(
    '--force', '-F', 'force',
    help='Overwrite any existing files in current working directory.',
    is_flag=True
)
@click.option(
    '--fast', '-j', 'fast',
    help='Use more CPU cores to build the application.',
    type=int,
    is_flag=False,
    flag_value=-1,
    default=1
)
@click.option(
    '--with-makefile', '-M', 'create_makefile',
    help='Create a Unikraft compatible Makefile.',
    is_flag=True
)
@click.pass_context
def cmd_up(ctx, workdir=None, name=None, plat=None, arch=None, initrd=None,
           background=False, paused=False, gdb=4123, dbg=False, virtio_nic=None,
           bridge=None, interface=None, dry_run=False, memory=64, cpu_sockets=1,
           cpu_cores=1, force=False, fast=False, create_makefile=False,
           template_app=None):
    """
    Configures, builds and runs an application for a selected architecture and
    platform.
    """

    kraft_list_preflight()

    if workdir is None and name is None:
        appdir = os.getcwd()
        name = os.path.basename(appdir)

    elif workdir is None:
        appdir = os.path.join(os.getcwd(), name)

    elif name is None:
        appdir = workdir
        name = os.path.basename(appdir)

    if arch is None:
        arch = ctx.obj.settings.get(KRAFTRC_CONFIGURE_ARCHITECTURE)

    if plat is None:
        plat = ctx.obj.settings.get(KRAFTRC_CONFIGURE_PLATFORM)

    # Check if the directory is non-empty and prompt for validation
    if util.is_dir_empty(appdir) is False and ctx.obj.assume_yes is False:
        if click.confirm('%s is a non-empty directory, would you like to continue?' % appdir):  # noqa: E501
            force = True
        else:
            logger.critical("Cannot create directory: %s" % appdir)
            sys.exit(1)

    try:
        kraft_list_pull(
            name=template_app,
            pull_dependencies=True
        )

        kraft_app_init(
            name=name,
            appdir=appdir,
            plat=plat,
            arch=arch,
            template_app=template_app,
            create_makefile=create_makefile,
            force_init=force
        )

        kraft_configure(
            env=ctx.obj.env,
            workdir=appdir,
            plat=plat,
            arch=arch,
            force_configure=force,
            show_menuconfig=False
        )

        kraft_build(
            workdir=appdir,
            fetch=True,
            prepare=True,
            fast=fast
        )

        kraft_run(
            appdir=appdir,
            plat=plat,
            arch=arch,
            initrd=initrd,
            background=background,
            paused=paused,
            dbg=dbg,
            gdb=gdb,
            virtio_nic=virtio_nic,
            bridge=bridge,
            interface=interface,
            dry_run=dry_run,
            # args=args,
            memory=memory,
            cpu_sockets=cpu_sockets,
            cpu_cores=cpu_cores,
        )

    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)
