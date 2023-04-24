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
import string
import sys

import click
import inquirer

from kraft.app import Application
from kraft.const import UK_CORE_ARCHS, UK_CORE_PLATS
from kraft.logger import logger
from kraft.target.target import Target


@click.pass_context # noqa
def kraft_run(ctx, appdir=None, target=None, plat=None, arch=None, initrd=None,
              background=False, paused=False, gdb=4123, dbg=False,
              virtio_nic=None, bridge=None, interface=None, dry_run=False,
              args=None, memory=64, cpu_sockets=1, cpu_cores=1, binary_path=None):
    """
    Starts the unikraft application once it has been successfully built.
    """

    app = Application.from_workdir(appdir)
    if not app.is_configured():
        if click.confirm('It appears you have not configured your application.  Would you like to do this now?', default=True):  # noqa: E501
            app.configure()

    if binary_path is None:
        if len(app.config.targets.all()) == 1:
            target = app.config.targets.all()[0]

        elif len(app.binaries) == 1:
            target = app.binaries[0]

        else:
            for t in app.config.targets.all():
                # Did the user specific a target-name?
                if target is not None and target == t.name:
                    target = t
                    break

                # Did the user specify arch AND plat combo? Does it exist?
                elif arch == t.architecture.name \
                        and plat == t.platform.name:
                    target = t
                    break

        # The user did not specify something
        if target is None:
            binaries = []
            for t in app.binaries:
                if not os.path.exists(t.binary):
                    continue

                binname = os.path.basename(t.binary_debug if dbg is True else t.binary)
                if t.name is not None:
                    binname = "%s (%s)" % (binname, t.name)

                binaries.append(binname)

            target_answer = None

            binaries = list(set(binaries))
            
            if len(binaries) == 0:
                print("""No binary found. 
    If the application is built successfully, this would possibly due to that you use the manual 'make menuconfig/kmenuconfig/...' to configure/build the application but use 'kraft run' to run it. Under such circumstance, 'make *config' will use the current directory name as the default binary name, but 'kraft' will take the value of 'name' field from 'kraft.yaml' to retrieve the binary file. This error will happen when they are not identical.
    Suggested fixes:
    1. update the 'name' field of 'kraft.yaml', or
    2. redo the 'make *config', and remember to change the image name based on 'kraft.yaml'
    3. specify the architecture, platform and binary path correspondingly using options specified in the help message (type 'kraft run -h' for details)
    """)
                raise Exception("Binary not found.")

            # Prompt user for binary selection
            if len(binaries) > 1:
                answers = inquirer.prompt([
                    inquirer.List(
                        'target',
                        message="Which target would you like to run?",
                        choices=binaries,
                    ),
                ])
                target_answer = answers['target']

            else:
                target_answer = binaries[0]

            # Work backwards from binary name
            for t in app.binaries:
                if target_answer == os.path.basename(t.binary):
                    target = t
                    break

    elif plat is not None and arch is not None:
        if arch not in UK_CORE_ARCHS:
            raise Exception("Architecture %s is not supported" % arch)
        if plat not in UK_CORE_PLATS:
            raise Exception("Platform %s is not supported" % plat)
            
        target = Target(architecture=arch, platform=plat)
        target.binary = binary_path # no need to check existance here, app.py:525 will gracefully check it

    else:
        print("Please speficy target platform and architecture together with binary path")
        raise Exception("platform/architecture not specified")

    app.run(
        target=target,
        initrd=initrd,
        background=background,
        paused=paused,
        gdb=gdb,
        dbg=dbg,
        virtio_nic=virtio_nic,
        bridge=bridge,
        interface=interface,
        dry_run=dry_run,
        args=args,
        memory=memory,
        cpu_sockets=cpu_sockets,
        cpu_cores=cpu_cores
    )


@click.command('run', short_help='Run the application.')
@click.option(
    '--target', '-t', 'target',
    help='Name of target architecture/platform.',
    metavar="TARGET"
)
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
    type=int,
    metavar="PORT"
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
    type=int,
    default=64
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
@click.option(
    '--binary-path', '-B', 'binary_path',
    help="The path of the binary file (by default kraft will use the name in kraft.yaml to retrieve the binary file).",
    metavar="PATH"
)
@click.argument('args', nargs=-1)
@click.pass_context
def cmd_run(ctx, target=None, plat=None, arch=None, initrd=None,
            background=False, paused=False, gdb=4123, dbg=False,
            virtio_nic=None, bridge=None, interface=None, dry_run=False,
            args=None, memory=64, cpu_sockets=1, cpu_cores=1, workdir=None,
            binary_path=None):

    if workdir is None:
        workdir = os.getcwd()

    try:
        kraft_run(
            appdir=workdir,
            target=target,
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
            binary_path=binary_path
        )

    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)
