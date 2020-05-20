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

from .build import kraft_build
from .configure import kraft_configure
from .init import kraft_init
from .run import kraft_run


@click.command('up', short_help='Configure, build and run an application.')
@click.argument('name', required=True)
@click.option('--plat',        '-p', 'target_plat', help='Target platform.', type=click.Choice(['linuxu', 'kvm', 'xen'], case_sensitive=True))  # noqa: E501
@click.option('--arch',        '-m', 'target_arch', help='Target architecture.', type=click.Choice(['x86_64', 'arm', 'arm64'], case_sensitive=True))  # noqa: E501
@click.option('--initrd',      '-i', 'initrd',      help='Provide an init ramdisk.')  # noqa: E501
@click.option('--background',  '-B', 'background',  help='Run in background.', is_flag=True)  # noqa: E501
@click.option('--paused',      '-P', 'paused',      help='Run the application in paused state.', is_flag=True)  # noqa: E501
@click.option('--gdb',         '-g', 'gdb',         help='Run a GDB server for the guest on specified port.', type=int)  # noqa: E501
@click.option('--dbg',         '-d', 'dbg',         help='Use unstriped unikernel', is_flag=True)  # noqa: E501
@click.option('--virtio-nic',  '-n', 'virtio_nic',  help='Attach a NAT-ed virtio-NIC to the guest.')  # noqa: E501
@click.option('--bridge',      '-b', 'bridge',      help='Attach a NAT-ed virtio-NIC an existing bridge.')  # noqa: E501
@click.option('--interface',   '-V', 'interface',   help='Assign host device interface directly as virtio-NIC to the guest.')  # noqa: E501
@click.option('--dry-run',     '-D', 'dry_run',     help='Perform a dry run.', is_flag=True)  # noqa: E501
@click.option('--memory',      '-M', 'memory',      help="Assign MB memory to the guest.", type=int)  # noqa: E501
@click.option('--cpu-sockets', '-s', 'cpu_sockets', help="Number of guest CPU sockets.", type=int)  # noqa: E501
@click.option('--cpu-cores',   '-c', 'cpu_cores',   help="Number of guest cores per socket.", type=int)  # noqa: E501
@click.option('--force',       '-F', 'force',       help='Overwrite any existing files in current working directory.', is_flag=True)  # noqa: E501
@click.option('--fast',        '-j', 'fast',        help='Use all CPU cores to build the application.', is_flag=True)  # noqa: E501
def up(name,
       target_plat,
       target_arch,
       initrd,
       background,
       paused,
       gdb,
       dbg,
       virtio_nic,
       bridge,
       interface,
       dry_run,
       memory,
       cpu_sockets,
       cpu_cores,
       force,
       fast):
    """
    Configures, builds and runs an application for a selected architecture and platform.
    """

    kraft_init(
        name=name,
        target_plat=target_plat,
        target_arch=target_arch,
        template_app=name,
        version=None,
        force_create=force
    )

    kraft_configure(
        target_plat=target_plat,
        target_arch=target_arch,
        force_configure=force,
        menuconfig=False
    )

    kraft_build(
        fast=fast
    )

    kraft_run(
        plat=target_plat,
        arch=target_arch,
        initrd=initrd,
        background=background,
        paused=paused,
        gdb=gdb,
        dbg=dbg,
        virtio_nic=virtio_nic,
        bridge=bridge,
        interface=interface,
        dry_run=dry_run,
        args=None,
        memory=memory,
        cpu_sockets=cpu_sockets,
        cpu_cores=cpu_cores
    )
