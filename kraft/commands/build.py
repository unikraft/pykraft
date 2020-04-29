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

from kraft.config import config
from kraft.logger import logger
from kraft.project import Project
from kraft.errors import KraftError
from kraft.kraft import kraft_context

@kraft_context
def kraft_build(ctx, fetch=True, prepare=True, target=None, fast=False):
    logger.debug("Building %s..." % ctx.workdir)

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
    
    if not project.is_configured():
        if click.confirm('It appears you have not configured your application.  Would you like to do this now?', default=True):
            try:
                project.configure(force_configure=True)

            except KraftError as e:
                logger.error(str(e))
                sys.exit(1)

    n_proc = None
    if fast:
        # This simply set the `-j` flag which signals to make to use all cores.
        n_proc = ""
    
    try:
        project.build(
            fetch=fetch,
            prepare=prepare,
            target=target,
            n_proc=n_proc
        )
    
    except KraftError as e:
        logger.error(str(e))
        sys.exit(1)

@click.command('build', short_help='Build the application.')
@click.option('--fetch/--no-fetch',           'fetch',   help='Run fetch step before build.', default=True)
@click.option('--prepare/--no-prepare',       'prepare', help='Run prepare step before build.',  default=True)
@click.option('--fast',                 '-j', 'fast',    help='Use all CPU cores to build the application.', is_flag=True)
@click.option('--noop',                 '-q', 'noop',    help='Do not run the build.', is_flag=True)
@click.argument('target', required=False)
def build(fetch=True, prepare=True, target=None, fast=False, noop=False):
    """
    Builds the Unikraft application for the target architecture and platform.
    """

    if noop:
        target = False

    kraft_build(
        fetch=fetch,
        prepare=prepare,
        target=target,
        fast=fast
    )