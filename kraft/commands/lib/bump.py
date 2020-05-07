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

import os
import sys

import click

from kraft.commands.list import update
from kraft.components.library import Library
from kraft.components.types import RepositoryType
from kraft.context import kraft_context
from kraft.errors import KraftError
from kraft.logger import logger
from kraft.utils import ClickOptionMutex


@click.command('bump', short_help='Update the library\'s version (experimental).')  # noqa: C901
@click.argument('path', required=False)
@click.option('--version',       '-V', 'version',       help='Set the version.', cls=ClickOptionMutex, not_required_if=['fast_forward', 'all'])  # noqa: E501
@click.option('--all',           '-A', 'bump_all',      help='Bump all libraries saved in cache (dangerous!).', cls=ClickOptionMutex, not_required_if=['version'], is_flag=True)  # noqa: E501
@click.option('--force-version', '-f', 'force_version', help='Force selection of version.', is_flag=True)  # noqa: E501
@click.option('--fast-forward',  '-F', 'fast_forward',  help='Upgrade library to latest version.', cls=ClickOptionMutex, not_required_if=['version'], is_flag=True)  # noqa: E501
@click.option('--build',         '-b', 'build',         help='Test the bump by building the library.', is_flag=True)  # noqa: E501
@kraft_context
def bump(ctx, path, version, bump_all, force_version, fast_forward, build):
    """
    Update an existing Unikraft library's source origin version (experimental).
    If --fast-forward is specified, the library will be upgraded to the latest
    known version.  Otherwise, and by default, the bump will increment by the
    smallest possible version.
    """

    if bump_all:
        # Pre-flight check determines if we are trying to work with nothing
        if ctx.cache.is_stale() and not ctx.assume_yes:
            if click.confirm('kraft caches are out-of-date.  Would you like to update?', default=True):
                update()

        elif ctx.assume_yes:
            update()

        for repo in ctx.cache.all():
            repo = ctx.cache.get(repo)

            if repo.type == RepositoryType.LIB:
                if ctx.assume_yes or click.confirm('Bump %s?' % repo.name):
                    if not ctx.dont_checkout:
                        repo.checkout()

                    try:
                        repo.bump(
                            fast_forward=fast_forward,
                            force_version=force_version,
                        )

                    except KraftError as e:
                        logger.critical(e)
                        sys.exit(1)

    else:
        if path is None:
            path = os.getcwd()

        try:
            library = Library.from_localdir(
                localdir=path,
            )

            library.checkout()

            library.bump(
                version=version,
                fast_forward=fast_forward,
                force_version=force_version,
            )

        except KraftError as e:
            logger.critical(e)
            sys.exit(1)
