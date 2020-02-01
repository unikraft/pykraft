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
#
# THIS HEADER MAY NOT BE EXTRACTED OR MODIFIED IN ANY WAY.

import click
from enum import Enum
import kraft.kraft as kraft
from kraft.repo import Repo
from datetime import datetime
from kraft.env import pass_environment
from kraft.component import KraftComponent

@click.command('list', short_help='List supported unikraft architectures, platforms, libraries or applications via remote repositories.')
@click.option('--core', '-c', is_flag=True, help='Display information about unikraft\'s core repository.')
@click.option('--archs', '-m', is_flag=True, help='List supported architectures.')
@click.option('--plats', '-p', is_flag=True, help='List supported platforms.')
@click.option('--libs', '-l', is_flag=True, help='List available libraries.')
@click.option('--apps', '-a', is_flag=True, help='List supported application runtime execution environments.')
# @click.option('--json', '-j', is_flag=True, help='Return values in JSON format.')
@click.option('--show-local', '-d', is_flag=True, help='Show the local location for the source.')
@click.option('--show-origin', '-r', is_flag=True, help='Show the remote location for the source.')
# @click.option('--import', '-i', '_import', help='Import a library from a specified path.')
@click.option('--paginate', '-n', is_flag=True, help='Paginate output')
@pass_environment
def cli(ctx, core, archs, plats, libs, apps, show_origin, show_local, paginate):
    """
    This subcommand retrieves lists of available architectures, platforms,
    libraries and applications supported by unikraft.  Use this command if you
    wish to determine (and then later select) the possible targets for your
    unikraft appliance.

    By default, this subcommand will list all possible targets.

    """
    
    # if _import:
    #     if core:
    #         _type = KraftComponent.APP
    #     elif archs:
    #         _type = KraftComponent.ARCH
    #     elif plats:
    #         _type = KraftComponent.PLAT
    #     elif libs:
    #         _type = KraftComponent.LIB
    #     else:
    #         _type = KraftComponent.APP
        
    #     ctx.cache.add_repo(Repo(
    #         remoteurl=_import,
    #         force_update=False,
    #         download=True,
    #         type=_type,
    #     ))

    # If no flags are set, show everything
    if core is False and archs is False and plats is False and libs is False and apps is False:
        core = archs = plats = libs = apps = True

    # Populate a matrix with all relevant columns and rows for each repository
    data = []

    for type, member in KraftComponent.__members__.items():
        columns = [member.plural.upper(), 'RELEASE', 'LAST UPDATED', 'LAST CHECKED']

        if show_local:
            columns.append('LOCATION')

        if show_origin:
            columns.append('ORIGIN')

        rows = []
        # rows = ctx.cache.repos(member)

        if core and member is KraftComponent.CORE:
            rows = ctx.cache.repos(member).items()

        elif archs and member is KraftComponent.ARCH:
            rows = ctx.cache.repos(member).items()

        elif plats and member is KraftComponent.PLAT:
            rows = ctx.cache.repos(member).items()

        elif libs and member is KraftComponent.LIB:
            rows = ctx.cache.repos(member).items()

        elif apps and member is KraftComponent.APP:
            rows = ctx.cache.repos(member).items()

        if len(rows) > 0:
            data.append(columns)

        for key, row in rows:
            line = [
              row.name,
              row.release,
              prettydate(row.last_updated),
              prettydate(row.last_checked),
            ]

            if show_local:
                if hasattr(row, 'localdir'):
                    line.append(row.localdir)
                else:
                    line.append('')
            if show_origin:
                if hasattr(row, 'remoteurl'):
                    line.append(row.remoteurl)
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
