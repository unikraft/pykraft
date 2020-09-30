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

from kraft.cmd.list import update
from kraft.error import KraftError
from kraft.lib import Library
from kraft.logger import logger
from kraft.types import ComponentType
from kraft.util import ClickOptionMutex
from kraft.manifest import maniest_from_name

from kraft.cmd.list import kraft_list_preflight
from kraft.cmd.list.pull import kraft_download_via_manifest

@click.pass_context


def kraft_lib_bump(ctx, workdir=None, version=None, bump_all=False,
                   force_version=False, fast_forward=False, build=False):
    """
    """

    if workdir is None:
        workdir = os.getcwd()

    library = Library.from_workdir(workdir)
    library.bump(
        version=version,
        fast_forward=fast_forward,
        force_version=force_version,
    )


@click.command('bump', short_help='Update a library\'s version (experimental).')  # noqa: C901
@click.option(
    '--version', '-v', 'version',
    help='Set the version.',
    cls=ClickOptionMutex,
    not_required_if=['fast_forward', 'all'],
    metavar="VERSION"
)
@click.option(
    '--all', '-A', 'bump_all',
    help='Bump all libraries (dangerous!).',
    cls=ClickOptionMutex,
    not_required_if=['version'],
    is_flag=True
)
@click.option(
    '--force-version', '-F', 'force_version',
    help='Force selection of version.',
    is_flag=True
)
@click.option(
    '--fast-forward', '-f', 'fast_forward',
    help='Upgrade library to latest version.',
    cls=ClickOptionMutex,
    not_required_if=['version'],
    is_flag=True
)
@click.option(
    '--build', '-b', 'build',
    help='Test the bump by building the library against helloworld.',
    is_flag=True
)
@click.argument(
    'lib',
    required=False,
    metavar="NAME|PATH"
)
@click.pass_context
def cmd_lib_bump(ctx, lib=None, version=None, bump_all=False,
                 force_version=False, fast_forward=False, build=False):
    """
    Update an existing Unikraft library's source origin version (experimental).

    If --fast-forward is specified, the library will be upgraded to the latest
    determined version.  Otherwise, and by default, the bump will increment by
    the smallest possible version.
    """

    kraft_list_preflight()

    try:
        if bump_all:
            for manifest_origin in ctx.obj.cache.all():
                manifest = ctx.obj.cache.get(manifest_origin)

                for _, item in manifest.items():
                    if item.type != ComponentType.LIB.shortname:
                        continue

                    if not (ctx.obj.assume_yes or click.confirm(
                            "Bump %s?" % item.name)):
                        continue
                        
                    kraft_download_via_manifest(
                        manifest=item,
                        use_git=True
                    )

                    kraft_lib_bump(
                        workdir=item.localdir,
                        force_version=force_version,
                        fast_forward=fast_forward,
                        build=build
                    )

        elif lib is not None and os.path.isdir(lib):
            kraft_lib_bump(
                workdir=lib,
                version=version,
                force_version=force_version,
                fast_forward=fast_forward,
            )

        elif lib is not None:
            manifests = maniest_from_name(lib)
            for manifest in manifests:
                if manifest.type != ComponentType.LIB.shortname:
                    continue

            if len(manifests) > 0 and version is not None:
                logger.warn("Ignoring --version flag")

            for manifest in manifests:
                kraft_download_via_manifest(
                    manifest=manifest,
                    use_git=True
                )

                kraft_lib_bump(
                    workdir=manifest.localdir,
                    version=version if len(manifests) == 1 else None,
                    force_version=force_version,
                    fast_forward=fast_forward,
                    build=build
                )
        else:
            kraft_lib_bump(
                workdir=os.getcwd(),
                version=version,
                force_version=force_version,
                fast_forward=fast_forward,
                build=build
            )


    except Exception as e:
        logger.error(e)
        if ctx.obj.verbose:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)