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

from github import Github
from datetime import datetime

from kraft.context import kraft_context

from kraft.logger import logger
from kraft.errors import KraftError
from kraft.components import Repository

from .init import kraft_init
from .configure import kraft_configure
from .build import kraft_build
from .run import kraft_run

@click.command('up', short_help='Configure, build and run an application.')
@click.argument('name', required=True)
@click.option('--plat', '-p', 'target_plat', help='Target platform.', type=click.Choice(['linuxu', 'kvm', 'xen'], case_sensitive=True))
@click.option('--arch', '-m', 'target_arch', help='Target architecture.', type=click.Choice(['x86_64', 'arm', 'arm64'], case_sensitive=True))
@click.option('--initrd', '-i', help='Provide an init ramdisk.')
@click.option('--background', '-X', is_flag=True, help='Run in background.')
@click.option('--paused', '-P', is_flag=True, help='Run the application in paused state.')
@click.option('--gdb', '-g', help='Run a GDB server for the guest on specified port.', type=int)
@click.option('--virtio-nic', '-n', help='Attach a NAT-ed virtio-NIC to the guest.')
@click.option('--bridge', '-b', help='Attach a NAT-ed virtio-NIC an existing bridge.')
@click.option('--interface', '-V', help='Assign host device interface directly as virtio-NIC to the guest.')
@click.option('--dry-run', '-D', is_flag=True, help='Perform a dry run.')
@click.option('--memory', '-M',  help="Assign MB memory to the guest.", type=int)
@click.option('--cpu-sockets', '-s',  help="Number of guest CPU sockets.", type=int)
@click.option('--cpu-cores', '-c',  help="Number of guest cores per socket.", type=int)
@click.option('--force', '-F', 'force_create', is_flag=True, help='Overwrite any existing files in current working directory.')
@click.option('--fast', '-j', is_flag=True, help='Use all CPU cores to build the application.')
@click.option('--with-dnsmasq', is_flag=True, help='Start a Dnsmasq server.')
@click.option('--ip-range', help='Set the IP range for Dnsmasq.', default='172.88.0.1,172.88.0.254')
@click.option('--ip-netmask', help='Set the netmask for Dnsmasq.', default='255.255.0.0')
@click.option('--ip-lease-time', help='Set the IP lease time for Dnsmasq.', default='12h')
def up(name, target_plat, target_arch, initrd, background, paused, gdb, virtio_nic, bridge, interface, dry_run, memory, cpu_sockets, cpu_cores, force_create, fast, with_dnsmasq, ip_range, ip_netmask, ip_lease_time):
    """
    Configures, builds and runs an application for a selected architecture and platform.
    """

    kraft_init(
        name=name,
        target_plat=target_plat,
        target_arch=target_arch,
        template_app=name,
        version=None,
        force_create=force_create
    )

    kraft_configure(
        target_plat=target_plat,
        target_arch=target_arch,
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
        virtio_nic=virtio_nic,
        bridge=bridge,
        interface=interface,
        dry_run=dry_run,
        args=None,
        memory=memory,
        cpu_sockets=cpu_sockets,
        cpu_cores=cpu_cores,
        with_dnsmasq=with_dnsmasq,
        ip_range=ip_range,
        ip_netmask=ip_netmask,
        ip_lease_time=ip_lease_time
    )

