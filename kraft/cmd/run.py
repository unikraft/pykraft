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
import platform
import sys

import click

from kraft.app import Application
from kraft.config import config
from kraft.const import UNIKERNEL_IMAGE_FORMAT
from kraft.error import KraftError
from kraft.error import RunnerError
from kraft.logger import logger


@click.pass_context # noqa
def kraft_run(ctx, appdir=None, plat=None, arch=None, initrd=None,
        background=False, paused=False, gdb=4123, dbg=False, virtio_nic=None,
        bridge=None, interface=None, dry_run=False, args=None, memory=64,
        cpu_sockets=1, cpu_cores=1):
    """
    Starts the unikraft application once it has been successfully built.
    """

    app = Application.from_workdir(appdir)

    target_architecture = None

    if len(app.architectures.all()) == 1:
        target_architecture = app.architectures.all()[0]
    else:
        for uk_architecture in app.architectures.all():
            if arch == uk_architecture.name:
                target_architecture = uk_architecture

    if target_architecture is None:
        raise KraftError('Application architecture not configured or set')
    
    target_platform = None

    if len(app.platforms.all()) == 1:
        target_platform = app.platforms.all()[0]
    else:
        for uk_platform in app.platforms.all():
            if plat == uk_platform.name:
                target_platform = uk_platform

    if target_platform is None:
        raise KraftError('Application platform not configured or set')
    
    unikernel = UNIKERNEL_IMAGE_FORMAT % (
        appdir,
        app.name,
        target_platform.name,
        target_architecture.name
    )

    if not os.path.exists(unikernel):
        raise KraftError('Could not find unikernel: %s' % unikernel)

    runner = target_platform.runner()
    runner.use_debug = dbg
    runner.architecture = target_architecture.name

    if initrd:
        runner.add_initrd(initrd)

    if virtio_nic:
        runner.add_virtio_nic(virtio_nic)

    if bridge:
        runner.add_bridge(bridge)

    if interface:
        runner.add_interface(interface)

    if gdb:
        runner.open_gdb(gdb)

    if memory:
        runner.set_memory(memory)

    if cpu_sockets:
        runner.set_cpu_sockets(cpu_sockets)

    if cpu_cores:
        runner.set_cpu_cores(cpu_cores)

    runner.unikernel = unikernel
    runner.execute(
        extra_args=args,
        background=background,
        paused=paused,
        dry_run=dry_run,
    )


@click.command('run', short_help='Run the application.')
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
    '--initrd', '-i', 'initrd',
    help='Provide an init ramdisk.',
    metavar="PATH"
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
    help='Run a GDB server for the guest at PORT.',
    type=int
)
@click.option(
    '--dbg', '-d', 'dbg',
    help='Use unstriped unikernel',
    is_flag=True
)
@click.option(
    '--virtio-nic', '-n', 'virtio_nic',
    help='Attach a NAT-ed virtio-NIC to the guest.',
    metavar="NAME"
)
@click.option(
    '--bridge', '-b', 'bridge',
    help='Attach a NAT-ed virtio-NIC an existing bridge.',
    metavar="NAME"
)
@click.option(
    '--interface', '-V', 'interface',
    help='Assign host device interface directly as virtio-NIC to the guest.',
    metavar="NAME"
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
    '--workdir', '-w', 'workdir',
    help='Specify an alternative directory for the library (default is cwd).',
    metavar="PATH"
)
@click.argument('args', nargs=-1)
@click.pass_context
def cmd_run(ctx, plat=None, arch=None, initrd=None, background=False,
        paused=False, gdb=4123, dbg=False, virtio_nic=None, bridge=None,
        interface=None, dry_run=False, args=None, memory=64, cpu_sockets=1,
        cpu_cores=1, workdir=None):
    
    if workdir is None:
        workdir = os.getcwd()

    try:
        kraft_run(
            appdir=workdir,
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
            args=args,
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