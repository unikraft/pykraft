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
from kraft.errors import ExecutorError
from kraft.kraft import kraft_context
from kraft.components import VolumeDriver
# from kraft.components.executor import Executor
# from kraft.components.network import start_dnsmasq_server
from kraft.constants import UNIKERNEL_IMAGE_FORMAT

@kraft_context
def kraft_run(ctx, plat, arch, initrd, background, paused, gdb, dbg, virtio_nic, 
    bridge, interface, dry_run, args, memory, cpu_sockets, cpu_cores):
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
            target_platform = platform
    
    if target_platform is None:
        logger.error('Application platform not configured or set')
        sys.exit(1)
    
    target_architecture = None

    for architecture in project.architectures.all():
        if arch == architecture.name:
            target_architecture = architecture
    
    if target_architecture is None:
        logger.error('Application architecture not configured or set')
        sys.exit(1)

    unikernel = UNIKERNEL_IMAGE_FORMAT % (
        ctx.workdir,
        project.name,
        target_platform.name,
        target_architecture.name
    )

    if not os.path.exists(unikernel):
        logger.error('Could not find unikernel: %s' % unikernel)
        logger.info('Have you tried running `kraft build`?')
        sys.exit(1)

    executor = target_platform.repository.executor
    executor.architecture = target_architecture.name
    executor.use_debug = dbg
    
    if initrd:
        executor.add_initrd(initrd)

    if virtio_nic:
        executor.add_virtio_nic(virtio_nic)

    if bridge:
        executor.add_bridge(bridge)

    if interface:
        executor.add_interface(interface)
    
    if gdb:
        executor.open_gdb(gdb)
    
    if memory:
        executor.set_memory(memory)
    
    if cpu_sockets:
        executor.set_cpu_sockets(cpu_sockets)
    
    if cpu_cores:
        executor.set_cpu_cores(cpu_cores)
    
    try:
        executor.unikernel = unikernel
        executor.execute(
            extra_args=args,
            background=background,
            paused=paused,
            dry_run=dry_run,
        )
    except ExecutorError as e:
        logger.error("Cannot execute: %s" % e)
        sys.exit(1)

@click.command('run', short_help='Run the application.')
@click.option('--plat', '-p', help='Target platform.', default='linuxu', type=click.Choice(['linuxu', 'kvm', 'xen'], case_sensitive=True), show_default=True)
@click.option('--arch', '-m', help='Target architecture.', default=lambda:platform.machine(), type=click.Choice(['x86_64', 'arm', 'arm64'], case_sensitive=True), show_default=True)
@click.option('--initrd', '-i', help='Provide an init ramdisk.')
@click.option('--background', '-X', is_flag=True, help='Run in background.')
@click.option('--paused', '-P', is_flag=True, help='Run the application in paused state.')
@click.option('--gdb', '-g', help='Run a GDB server for the guest at PORT.', type=int)
@click.option('--dbg', '-d', is_flag=True, help='Use unstriped unikernel')
@click.option('--virtio-nic', '-n', help='Attach a NAT-ed virtio-NIC to the guest.')
@click.option('--bridge', '-b', help='Attach a NAT-ed virtio-NIC an existing bridge.')
@click.option('--interface', '-V', help='Assign host device interface directly as virtio-NIC to the guest.')
@click.option('--dry-run', '-D', is_flag=True, help='Perform a dry run.')
@click.option('--memory', '-M',  help="Assign MB memory to the guest.", type=int)
@click.option('--cpu-sockets', '-s',  help="Number of guest CPU sockets.", type=int)
@click.option('--cpu-cores', '-c',  help="Number of guest cores per socket.", type=int)
@click.argument('args', nargs=-1)
def run(plat, arch, initrd, background, paused, gdb, dbg, virtio_nic, bridge,
    interface, dry_run, args, memory, cpu_sockets, cpu_cores):
    
    kraft_run(
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