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

import sys

import click

from kraft.config import config
from kraft.errors import KraftError
from kraft.kraft import kraft_context
from kraft.logger import logger
from kraft.project import Project


@kraft_context
def kraft_configure(ctx,
                    target_plat,
                    target_arch,
                    force_configure,
                    menuconfig):
    """
    Populates the local .config with the default values for the target application.
    """

    logger.debug("Configuring %s..." % ctx.workdir)

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

    if project.is_configured() \
        and force_configure is False \
            and menuconfig is False:
        if click.confirm('%s is already configured, would you like to overwrite configuration?' % ctx.workdir): # noqa
            force_configure = True

        else:
            logger.error('Cancelling!')
            sys.exit(1)

    if menuconfig:
        project.menuconfig()

    else:
        try:
            project.configure(
                target_arch=target_arch,
                target_plat=target_plat
            )
        except KraftError as e:
            logger.error(str(e))
            sys.exit(1)


@click.command('configure', short_help='Configure the application.')
@click.option('--plat',       '-p', 'target_plat',     help='Target platform.')  # noqa: E501
@click.option('--arch',       '-m', 'target_arch',     help='Target architecture.', type=click.Choice(['x86_64', 'arm', 'arm64'], case_sensitive=True))  # noqa: E501
@click.option('--force',      '-F', 'force_configure', help='Force writing new configuration.', is_flag=True)  # noqa: E501
@click.option('--menuconfig', '-k', 'menuconfig',      help='Use Unikraft\'s ncurses Kconfig editor.', is_flag=True)  # noqa: E501
def configure(target_plat, target_arch, force_configure,  menuconfig):
    kraft_configure(
        target_plat=target_plat,
        target_arch=target_arch,
        force_configure=force_configure,
        menuconfig=menuconfig
    )
