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
import platform
from enum import Enum

from kraft.config import config
from kraft.logger import logger
from kraft.project import Project
from kraft.errors import KraftError
from kraft.kraft import kraft_context
from kraft.executor import Executor

from kraft.constants import UNIKERNEL_IMAGE_FORMAT

@click.command('run', short_help='Run the application.')
@click.option('--plat', '-p', default='linuxu', help='Target platform.', type=click.Choice(['linuxu', 'kvm', 'xen'], case_sensitive=True), show_default=True)
@click.option('--arch', '-m', help='Target architecture.', default=lambda:platform.machine(), type=click.Choice(['x86_64', 'arm', 'arm64'], case_sensitive=True), show_default=True)
@click.option('--initrd', '-i', help='Provide an init ramdisk.')
@click.option('--background', '-X', is_flag=True, help='Run in background.')
@click.option('--paused', '-P', is_flag=True, help='Run the application in paused state.')
@click.option('--gdb', '-g', help='Run a GDB server for the guest at PORT.', type=int)
@click.option('--virtio-nic', '-n', help='Attach a NAT-ed virtio-NIC to the guest.')
@click.option('--bridge', '-b', help='Attach a NAT-ed virtio-NIC an existing bridge.')
@click.option('--interface', '-V', help='Assign host device interface directly as virtio-NIC to the guest.')
@click.option('--block-storage', '-d', help='Attach a block storage device based on a raw device.')
@click.option('--dry-run', '-D', is_flag=True, help='Perform a dry run.')
@click.argument('args', nargs=-1)
@kraft_context
def run(ctx, plat, arch, initrd, background, paused, gdb, virtio_nic, bridge, interface, block_storage, dry_run, args):
    """
    Starts the unikraft application once it has been successfully
    built.
    """

    try:
        project = Project.from_config(
            ctx.workdir,
            config.load(
                config.find(ctx.workdir, None, ctx.env)
            )
        )

    except KraftError as e:
        logger.error(str(e))
        sys.exit(1)

    target_platform = None

    for platform in project.platforms.all():
        if plat == platform.name:
            target_platform = plat
    
    if target_platform is None:
        logger.error('Application platform not available: %s' % plat)
        sys.exit(1)
    
    target_architecture = None

    for architecture in project.architectures.all():
        if arch == architecture.name:
            target_architecture = arch
    
    if target_architecture is None:
        logger.error('Application architecture not available: %s' % arch)
        sys.exit(1)

    unikernel = UNIKERNEL_IMAGE_FORMAT % (
        ctx.workdir,
        project.name,
        target_platform,
        target_architecture
    )

    if not os.path.exists(unikernel):
        logger.error('Could not find unikernel: %s' % unikernel)
        sys.exit(1)

    executor = Executor(
        kernel=unikernel,
        architecture=arch,
        platform=plat
    )

    if initrd:
        executor.add_initrd(initrd)

    if virtio_nic:
        executor.add_virtio_nic(virtio_nic)

    if bridge:
        executor.add_bridge(bridge)

    if interface:
        executor.add_interface(interface)

    if block_storage:
        executor.add_block_storage(block_storage)
    
    if gdb:
        executor.open_gdb(gdb)

    executor.execute(
        extra_args=args,
        background=background,
        paused=paused,
        dry_run=dry_run
    )