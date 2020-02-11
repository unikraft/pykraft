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

import sys
import click
from enum import Enum
from datetime import datetime

from kraft.context import kraft_context

from kraft.component import Component
from kraft.components import Repository

@click.command('list', short_help='List archs, platforms, libraries or applications.')
@click.option('--core', '-c', is_flag=True, help='Display information about Unikraft\'s core repository.')
# @click.option('--archs', '-m', is_flag=True, help='List supported architectures.')
@click.option('--plats', '-p', is_flag=True, help='List supported platforms.')
@click.option('--libs', '-l', is_flag=True, help='List supported libraries.')
@click.option('--apps', '-a', is_flag=True, help='List supported application runtime execution environments.')
# @click.option('--json', '-j', is_flag=True, help='Return values in JSON format.')
@click.option('--show-local', '-d', is_flag=True, help='Show local source path.')
@click.option('--show-origin', '-r', is_flag=True, help='Show remote source location.')
# @click.option('--import', '-i', '_import', help='Import a library from a specified path.')
@click.option('--paginate', '-n', is_flag=True, help='Paginate output.')
@kraft_context
def list(ctx, core, plats, libs, apps, show_origin, show_local, paginate):
    """
    This subcommand retrieves lists of available architectures, platforms,
    libraries and applications supported by unikraft.  Use this command if you
    wish to determine (and then later select) the possible targets for your
    unikraft appliance.

    By default, this subcommand will list all possible targets.

    """
    # TODO: Architectures should be dynamically generated from the Unikraft
    # source code.
    archs = False

    # If no flags are set, show everything
    if core is False and archs is False and plats is False and libs is False and apps is False:
        core = archs = plats = libs = apps = True

    # Populate a matrix with all relevant columns and rows for each repository
    repos = {}
    data = []

    for repo in ctx.cache.all():
        repo = ctx.cache.get(repo)

        if not repo.type in repos:
            repos[repo.type] = []
        
        repos[repo.type].append(repo)
        
    for type, member in Component.__members__.items():
        columns = [member.plural.upper(), 'RELEASE', 'LAST CHECKED']

        if show_local:
            columns.append('LOCATION')

        if show_origin:
            columns.append('ORIGIN')

        rows = []

        if core and member is Component.CORE and member in repos:
            rows = repos[member]

        elif archs and member is Component.ARCH and member in repos:
            rows = repos[member]

        elif plats and member is Component.PLAT and member in repos:
            rows = repos[member]

        elif libs and member is Component.LIB and member in repos:
            rows = repos[member]

        elif apps and member is Component.APP and member in repos:
            rows = repos[member]
        
        if len(rows) > 0:
            data.append(columns)

        for row in rows:
            line = [
                row.name,
                row.latest_release,
                # prettydate(row.last_updated),
                prettydate(row.last_checked),
            ]

            if show_local:
                if hasattr(row, 'localdir'):
                    line.append(row.localdir)
                else:
                    line.append('')
            if show_origin:
                if hasattr(row, 'source'):
                    line.append(row.source)
                else:
                    line.append('')

            data.append(line)

        # Line break
        if len(rows) > 0:
            colnum = 4
            if show_local:
                colnum += 1
            if show_origin:
                colnum += 1

            data.append([" "] * colnum)

    output = pretty_columns(data)

    if paginate:
        click.echo_via_pager(output)
    else:
        print(output)

def pretty_columns(data = []):
    widths = [max(map(len, col)) for col in zip(*data)]
    output = ""

    for row in data:
        output += "\t".join((val.ljust(width) for val, width in zip(row, widths))) + "\n"

    return output

def prettydate(date=None):
    if date is None:
        return 'Never'

    diff = datetime.utcnow() - date
    s = diff.seconds

    if diff.days > 7 or diff.days < 0:
        return date.strftime('%d %b %y')
    elif diff.days == 1:
        return '1 day ago'
    elif diff.days > 1:
        return '{} days ago'.format(round(diff.days))
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{} seconds ago'.format(round(s))
    elif s < 120:
        return '1 minute ago'
    elif s < 3600:
        return '{} minutes ago'.format(round(s/60))
    elif s < 7200:
        return '1 hour ago'
    else:
        return '{} hours ago'.format(round(s/3600))
