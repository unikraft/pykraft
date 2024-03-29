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
from kraft.logger import logger
from kraft.util import make_progressbar


@click.command('clean', short_help='Clean the application.')
@click.option(
    '--workdir', '-w', 'workdir',
    help='Specify an alternative working directory for the application',
    metavar="PATH"
)
@click.option(
    '--proper', '-p', 'proper',
    help='Delete the build directory.',
    is_flag=True,
)
@click.option(
    '--dist', '-d', 'dist',
    help='Delete the build directory and configuration files.',
    is_flag=True,
)
@click.option(
    '--progress/--no-progress', 'progress',
    help='Show progress of build.',
    default=True
)
@click.argument('libs', nargs=-1)
@click.pass_context
def cmd_clean(ctx, workdir=None, proper=False, dist=False, progress=True,
              libs=None):
    """
    Clean the build artifacts of a Unikraft unikernel application.
    """

    if workdir is None:
        workdir = ctx.obj.workdir

    try:
        kraft_clean(
            workdir=workdir,
            proper=proper,
            dist=dist,
            progress=progress,
            libs=libs,
        )

    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)


@click.pass_context
def kraft_clean(ctx, workdir=None, proper=False, dist=False, progress=True,
                libs=None):
    """
    Cleans the build artifacts of a Unikraft unikernel.
    """

    if workdir is None or os.path.exists(workdir) is False:
        raise ValueError("working directory is empty: %s" % workdir)

    logger.debug("Cleaning %s..." % workdir)

    app = Application.from_workdir(workdir)

    if progress:
        if proper:
            make_progressbar(app.make_raw(
                extra="properclean"
            ))

        elif dist:
            make_progressbar(app.make_raw(
                extra="distclean"
            ))

        else:
            if len(libs) is not None and len(libs) > 0:
                for lib in list(libs):
                    make_progressbar(app.make_raw(
                        extra="clean-lib%s" % lib
                    ))

            else:
                make_progressbar(app.make_raw(
                    extra="clean"
                ))

    else:
        app.clean(
            proper=proper,
            dist=dist
        )
