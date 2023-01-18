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
from kraft.cmd.list import kraft_list_preflight
from kraft.const import UNIKRAFT_BUILDDIR
from kraft.logger import logger
from kraft.util import make_progressbar


@click.pass_context
def kraft_build(ctx, verbose=False, workdir=None, fetch=True, prepare=True,
                progress=True, target=None, fast=False, force_build=False):
    """
    """
    if workdir is None or os.path.exists(workdir) is False:
        raise ValueError("working directory is empty: %s" % workdir)

    logger.debug("Building %s..." % workdir)

    app = Application.from_workdir(workdir, force_build)

    if not app.is_configured():
        if click.confirm('It appears you have not configured your application.  Would you like to do this now?', default=True):  # noqa: E501
            app.configure()

    n_proc = None
    if fast:
        n_proc = int(fast)

    if fetch:
        app.fetch()

    if prepare:
        app.prepare()

    if progress:
        return_code = make_progressbar(app.make_raw(
            verbose=verbose,
            n_proc=n_proc
        ))

    else:
        return_code = app.build(
            target=target,
            n_proc=n_proc
        )

    if return_code > 0:
        sys.exit(return_code)

    print("\nSuccessfully built unikernels:\n")

    for target in app.binaries:
        if not os.path.exists(target.binary):
            continue

        print("  => %s/%s" % (
            UNIKRAFT_BUILDDIR,
            os.path.basename(target.binary)
        ))
        print("  => %s/%s (with symbols)" % (
            UNIKRAFT_BUILDDIR,
            os.path.basename(target.binary_debug)
        ))

    print("\nTo instantiate, use: kraft run\n")


@click.command('build', short_help='Build the application.')
@click.option(
    '--verbose', '-v', 'verbose_build',
    help='Verbose build',
    is_flag=True
)
@click.option(
    '--fetch/--no-fetch', 'fetch',
    help='Run fetch step before build.',
    default=True
)
@click.option(
    '--prepare/--no-prepare', 'prepare',
    help='Run prepare step before build.',
    default=True
)
@click.option(
    '--progress/--no-progress', 'progress',
    help='Show progress of build.',
    default=True
)
@click.option(
    '--fast', '-j', 'fast',
    help='Use more CPU cores to build the application.',
    type=int,
    is_flag=False,
    flag_value=-1,
    default=1
)
@click.option(
    '--force', '-F', 'force_build',
    help='Force the build of the unikernel.',
    is_flag=True
)
@click.argument('target', required=False)
@click.pass_context
def cmd_build(ctx, verbose_build=False, fetch=True, prepare=True,
              progress=True, target=None, fast=False, force_build=False):
    """
    Builds the Unikraft application for the target architecture and platform.
    """

    kraft_list_preflight()

    try:
        kraft_build(
            workdir=ctx.obj.workdir,
            verbose=verbose_build,
            fetch=fetch,
            prepare=prepare,
            progress=progress,
            target=target,
            fast=fast,
            force_build=force_build
        )

    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)
