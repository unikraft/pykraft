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

import json
import os
import sys
import threading
from datetime import datetime

import click
from atpbar import flush
from github import Github

from kraft.component import Component
from kraft.app import Application
from kraft.arch import Architecture
from kraft.const import DATE_FORMAT
from kraft.const import UK_GITHUB_ORG
from kraft.const import UNIKRAFT_RELEASE_STABLE
from kraft.error import KraftError
from kraft.lib import Library
from kraft.logger import logger
from kraft.plat import Platform
from kraft.types import ComponentType
from kraft.types import str_to_component_type
from kraft.util import pretty_columns
from kraft.util import prettydate
from kraft.unikraft import Unikraft
from kraft.util import ClickReaderOption
from kraft.util import ClickWriterOption
from kraft.util import ClickWriterCommand

from .update import kraft_update


@click.group(
    'list',
    short_help='List architectures, platforms, libraries or applications.',
    invoke_without_command=True,
    cls=ClickWriterCommand
)
@click.option(
    '--installed', '-i', 'show_installed',
    help='Display only installed components.',
    is_flag=True
)
@click.option(
    '--core', '-c', 'show_core',
    help='Display information about Unikraft\'s core repository.',
    is_flag=True
)
# @click.option(
#   '--archs', '-m', 'show_archs',
#   help='List supported architectures.',
#   is_flag=True
# )
@click.option(
    '--plats', '-p', 'show_plats',
    help='List supported platforms.',
    is_flag=True
)
@click.option(
    '--libs', '-l', 'show_libs',
    help='List supported libraries.',
    is_flag=True
)
@click.option(
    '--apps', '-a', 'show_apps',
    help='List supported application runtime execution environments.', is_flag=True
)
# @click.option(
# '--json', '-j', 'show_json',
#   help='Return values in JSON format.',
#   is_flag=True
# )
@click.option(
    '--show-local', '-d', 'show_local',
    help='Show local source path.',
    is_flag=True
)
@click.option(
    '--paginate', '-n', 'paginate',
    help='Paginate output.',
    is_flag=True
)
@click.option(
    '--this', '-t',
    cls=ClickReaderOption,
    is_flag=True,
    help='Show the components for this application (default is cwd).'
)
@click.option(
    '--this_set',
    cls=ClickWriterOption,
    help='Show the components for this application.',
    metavar='PATH'
)
@click.option(
    '--json', '-j', 'return_json',
    help='Return output as JSON.',
    is_flag=True
)
@click.pass_context
def cmd_list(ctx, show_installed=False, show_core=False, show_plats=False,
        show_libs=False, show_apps=False, show_local=False, paginate=False,
        this=False, this_set=None, return_json=False):
    """
    Retrieves lists of available architectures, platforms, libraries and
    applications supported by unikraft.  Use this command if you wish to
    determine (and then later select) the possible targets for your unikraft
    application.

    By default, this subcommand will list all possible targets.

    """
    if ctx.invoked_subcommand is None:
        kraft_list_preflight()

        show_archs = False
        
        # If no flags are set, show everything
        if show_core is False \
            and show_archs is False \
            and show_plats is False \
            and show_libs is False \
            and show_apps is False:
            show_core = show_archs = show_plats = show_libs = show_apps = True

        # Populate a matrix with all relevant columns and rows for each
        # component.
        components = {}
        data = []
        data_json = {}

        if this or this_set is not None:
            workdir = os.getcwd()
            if this_set is not None:
                workdir = this_set

            try:
                app = Application.from_workdir(workdir)
                
                for manifest in app.manifests:
                    if manifest.type not in components:
                        components[manifest.type] = []
                    components[manifest.type].append(manifest)

            except KraftError as e:
                logger.error(str(e))
                sys.exit(1)

        else:
            for manifest_origin in ctx.obj.cache.all():
                manifest = ctx.obj.cache.get(manifest_origin)

                for _, item in manifest.items():
                    if item.type not in components:
                        components[item.type] = []
                
                    components[item.type].append(item)

        for type, member in ComponentType.__members__.items():
            columns = [
                click.style(member.plural.upper(), fg='white'),
                click.style('VERSION ', fg='white'),
                click.style('RELEASED', fg='white'),
                click.style('LAST CHECKED', fg='white')
            ]

            if show_local:
                columns.append(click.style('LOCATION', fg='white'))

            rows = []
            components_showing = 0

            if member.shortname in components and (\
                (show_core and member is ComponentType.CORE) or \
                (show_archs and member is ComponentType.ARCH) or \
                (show_plats and member is ComponentType.PLAT) or \
                (show_libs and member is ComponentType.LIB) or \
                (show_apps and member is ComponentType.APP)):
                rows = components[member.shortname]

            # if len(rows) > 0:
            data.append(columns)

            for row in rows:
                installed = False
                install_error = False
                localdir = str_to_component_type(row.type).localdir()

                if row.type != ComponentType.CORE:
                    localdir = os.path.join(localdir, row.name)

                if os.path.isdir(localdir):
                    installed = True
                    if len(os.listdir(localdir)) == 0:
                        install_error = True
                        logger.warn("%s directory is empty: %s "
                            % (row.name, localdir))

                if return_json:
                    if member.plural not in data_json:
                        data_json[member.plural] = []

                    row_json = {
                        'name': row.name,
                        'latest': row.latest_release,
                        'last_checked': row.last_checked.strftime(DATE_FORMAT),
                        'known_versions': row.known_versions
                    }

                    if show_local:
                        if hasattr(row, 'localdir'):
                            row_json.update({'localdir': row.localdir})

                    if not show_installed or (installed and show_installed):
                        data_json[member.plural].append(row_json)
                        components_showing += 1

                else:
                    latest_release = None
                    if UNIKRAFT_RELEASE_STABLE in row.dists.keys():
                        latest_release = row.dists[UNIKRAFT_RELEASE_STABLE].latest
                    else:
                        pass

                    line = [
                        click.style(row.name, fg='yellow' if install_error else 'green' if installed else 'red'),
                        click.style(latest_release.version if latest_release is not None else "", fg='white'),
                        click.style(prettydate(latest_release.timestamp) if latest_release is not None else "", fg='white'),
                        click.style(prettydate(row.last_checked), fg='white'),
                    ]

                    if show_local:
                        line.append(click.style(localdir if installed else '', fg='white'))

                    if not show_installed or (installed and show_installed):
                        data.append(line)
                        components_showing += 1

            # Delete component headers with no rows
            if components_showing == 0 and len(data) > 0:
                del data[-1]

            # Line break
            elif len(rows) > 0:
                data.append([click.style("", fg='white')] * len(columns))

        if return_json:
            click.echo(json.dumps(data_json))
            
        else:
            output = pretty_columns(data)

            if len(data) == 0:
                logger.info("Nothing to show")
            elif paginate:
                click.echo_via_pager(output)
            else:
                click.echo(output[:-1])


# Pre-flight check determines if we are trying to work with nothing
@click.pass_context
def kraft_list_preflight(ctx):
    if ctx.obj.cache.is_stale():
        if click.confirm(
            'kraft caches are out-of-date. Would you like to update?',
            default=True):
            kraft_update()
