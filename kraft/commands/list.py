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

import json
import os
import sys
import threading
from datetime import datetime

import click
from atpbar import flush
from github import Github

from kraft.components.repository import Repository
from kraft.components.types import RepositoryType
from kraft.constants import DATE_FORMAT
from kraft.constants import UK_GITHUB_ORG
from kraft.context import kraft_context
from kraft.errors import KraftError
from kraft.logger import logger


@click.command('list', short_help='List architectures, platforms, libraries or applications.')  # noqa: E501,C901
@click.option('--core',        '-c', 'core',         help='Display information about Unikraft\'s core repository.', is_flag=True)  # noqa: E501
# @click.option('--archs',       '-m',                 help='List supported architectures.', is_flag=True)  # noqa: E501
@click.option('--plats',       '-p', 'plats',        help='List supported platforms.', is_flag=True)  # noqa: E501
@click.option('--libs',        '-l', 'libs',         help='List supported libraries.', is_flag=True)  # noqa: E501
@click.option('--apps',        '-a', 'apps',         help='List supported application runtime execution environments.', is_flag=True)  # noqa: E501
# @click.option('--json',        '-j', 'json',         help='Return values in JSON format.', is_flag=True)  # noqa: E501
@click.option('--show-local',  '-d', 'show_local',   help='Show local source path.', is_flag=True)  # noqa: E501
@click.option('--show-origin', '-r', 'show_origin',  help='Show remote source location.', is_flag=True)  # noqa: E501
# @click.option('--import',      '-i', '_import',      help='Import a library from a specified path.')  # noqa: E501
@click.option('--paginate',    '-n', 'paginate',     help='Paginate output.', is_flag=True)  # noqa: E501
@click.option('--update',      '-u', 'force_update', help='Retrieves lists of available architectures, platforms libraries and applications supported by Unikraft.', is_flag=True)  # noqa: E501
@click.option('--flush',       '-F', 'force_flush',  help='Cleans the cache and lists.', is_flag=True)  # noqa: E501
@click.option('--json',        '-j', 'return_json',  help='Return output as JSON.', is_flag=True)  # noqa: E501
@kraft_context
def list(ctx,
         core,
         plats,
         libs,
         apps,
         show_origin,
         show_local,
         paginate,
         force_update,
         force_flush,
         return_json):
    """
    Retrieves lists of available architectures, platforms, libraries and applications
    supported by unikraft.  Use this command if you wish to determine (and then
    later select) the possible targets for yourunikraft application.

    By default, this subcommand will list all possible targets.

    """

    # Pre-flight check determines if we are trying to work with nothing
    if ctx.cache.is_stale() and not force_update:
        if click.confirm('kraft caches are out-of-date.  Would you like to update?', default=True):
            update()
    elif force_update:
        update()

    # TODO: Architectures should be dynamically generated from the Unikraft
    # source code.
    archs = False

    # If no flags are set, show everything
    if core is False and archs is False and plats is False and libs is False and apps is False:
        core = archs = plats = libs = apps = True

    # Populate a matrix with all relevant columns and rows for each repository
    repos = {}
    data = []
    data_json = {}

    for repo in ctx.cache.all():
        repo = ctx.cache.get(repo)

        if repo.type not in repos:
            repos[repo.type] = []

        repos[repo.type].append(repo)

    for type, member in RepositoryType.__members__.items():
        columns = [member.plural.upper(), 'RELEASE', 'LAST CHECKED']

        if show_local:
            columns.append('LOCATION')

        if show_origin:
            columns.append('ORIGIN')

        rows = []

        if core and member is RepositoryType.CORE and member in repos:
            rows = repos[member]

        elif archs and member is RepositoryType.ARCH and member in repos:
            rows = repos[member]

        elif plats and member is RepositoryType.PLAT and member in repos:
            rows = repos[member]

        elif libs and member is RepositoryType.LIB and member in repos:
            rows = repos[member]

        elif apps and member is RepositoryType.APP and member in repos:
            rows = repos[member]

        if len(rows) > 0:
            data.append(columns)

        for row in rows:
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

                if show_origin:
                    if hasattr(row, 'source'):
                        row_json.update({'source': row.source})

                data_json[member.plural].append(row_json)
            else:
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

    if return_json:
        print(json.dumps(data_json))
    else:
        output = pretty_columns(data)

        if paginate:
            click.echo_via_pager(output)
        else:
            print(output)


@kraft_context
def update(ctx):
    if 'UK_KRAFT_GITHUB_TOKEN' in os.environ:
        github = Github(os.environ['UK_KRAFT_GITHUB_TOKEN'])
    else:
        github = Github()

    org = github.get_organization(UK_GITHUB_ORG)
    threads = []

    def clone_repo(ctx, clone_url=None):
        with ctx:
            logger.info("Probing %s..." % clone_url)

            try:
                Repository.from_source_string(
                    source=clone_url,
                    force_update=True
                )
            except KraftError as e:
                logger.error("Could not add repository: %s: %s" % (repo.clone_url, str(e)))

    for repo in org.get_repos():
        # There is one repository which contains the codebase to kraft
        # itself (this code!) that is returned in this iteration.  Let's
        # filter it out here so we don't receive a prompt for an invalid
        # repository.
        if repo.clone_url == 'https://github.com/unikraft/kraft.git':
            continue

        t = threading.Thread(target=clone_repo, args=(ctx, repo.clone_url, ))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    if sys.stdout.isatty():
        flush()


def pretty_columns(data=[]):
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
