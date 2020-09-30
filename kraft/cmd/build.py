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
from kraft.config import config
from kraft.error import KraftError
from kraft.logger import logger

from kraft.cmd.list import kraft_list_preflight

@click.pass_context
def kraft_build(ctx, workdir=None, fetch=True, prepare=True, target=None,
        fast=False):
    """
    """
    if workdir is None or os.path.exists(workdir) is False:
        raise ValueError("working directory is empty: %s" % workdir)

    logger.debug("Building %s..." % workdir)

    app = Application.from_workdir(workdir)

    if not app.is_configured():
        if click.confirm('It appears you have not configured your application.  Would you like to do this now?', default=True):  # noqa: E501
            app.configure()
    
    n_proc = None
    if fast:
        # This simply set the `-j` flag which signals to make to use all cores.
        n_proc = 0

    app.build(
        fetch=fetch,
        prepare=prepare,
        target=target,
        n_proc=n_proc
    )



@click.command('build', short_help='Build the application.')
@click.option(
    '--fetch/--no-fetch','fetch',
    help='Run fetch step before build.',
    default=True
)
@click.option(
    '--prepare/--no-prepare','prepare',
    help='Run prepare step before build.',
    default=True
)
@click.option(
    '--fast','-j', 'fast',
    help='Use all CPU cores to build the application.',
    is_flag=True
)
@click.argument('target', required=False)
@click.pass_context
def cmd_build(ctx, fetch=True, prepare=True, target=None, fast=False):
    """
    Builds the Unikraft application for the target architecture and platform.
    """

    kraft_list_preflight()

    try:
        kraft_build(
            workdir=ctx.obj.workdir,
            fetch=fetch,
            prepare=prepare,
            target=target,
            fast=fast
        )

    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)