# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <a.jung@lancs.ac.uk>
#
# Copyright (c) 2021, Lancaster University.  All rights reserved.
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


@click.pass_context
def kraft_lib_remove(ctx, workdir=None, lib=None, purge=False):
    if workdir is None or os.path.exists(workdir) is False:
        raise ValueError("working directory is empty: %s" % workdir)

    if isinstance(lib, tuple):
        lib = list(lib)

    if isinstance(lib, list):
        for l in lib:  # noqa: E741
            if not kraft_lib_remove(workdir, l, purge):
                return False
        return True

    app = Application.from_workdir(
        workdir,
        force_init=True,
        use_versions=[lib]  # override version if already present
    )

    return app.remove_lib(lib, purge=purge)


@click.command('remove', short_help='Remove a library from the project.')
@click.option(
    '--workdir', '-w', 'workdir',
    help='Specify an alternative directory for the application [default is cwd].',
    metavar="PATH"
)
@click.option(
    '--purge', '-P', 'purge',
    help='Removes the source files for the library.',
    is_flag=True,
)
@click.argument('lib', required=False, nargs=-1)
@click.pass_context
def cmd_lib_remove(ctx, workdir=None, lib=None, purge=False):
    """
    Remove a library from the unikraft application project.
    """

    if workdir is None:
        workdir = os.getcwd()

    try:
        if not kraft_lib_remove(workdir=workdir, lib=lib, purge=purge):
            sys.exit(1)

    except Exception as e:
        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())
        else:
            logger.critical(str(e))

        sys.exit(1)
