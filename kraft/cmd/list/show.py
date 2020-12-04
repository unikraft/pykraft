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
import textwrap

import click

from .list import kraft_list_preflight
from kraft.const import LIST_DESC_WIDTH
from kraft.logger import logger
from kraft.types import break_component_naming_format
from kraft.util import pretty_columns
from kraft.util import prettydate


@click.command('show', short_help='Show a unikraft component.')  # noqa: C901
@click.option(
    '--json', '-j', 'return_json',
    help='Return output as JSON.',
    is_flag=True
)
@click.argument('name')
@click.pass_context
def cmd_list_show(ctx, return_json=False, name=None):
    """
    Show the details of a component in a remote repository.
    """

    kraft_list_preflight()

    components = list()
    type, name, _, _ = break_component_naming_format(name)

    for manifest_origin in ctx.obj.cache.all():
        manifest = ctx.obj.cache.get(manifest_origin)

        for _, component in manifest.items():
            if (type is None or
                    (type is not None
                        and type == component.type)) \
                    and component.name == name:
                components.append(component)

    if len(components) == 0:
        logger.error("Unknown component name: %s" % name)
        sys.exit(1)

    if return_json:
        data_json = []
        for _, component in enumerate(components):
            data_json.append(component.__getstate__())

        click.echo(json.dumps(data_json))

    else:
        for i, component in enumerate(components):

            # print seperator
            if len(components) > 1 and i > 0 and not return_json:
                click.echo("---")

            table = list()
            table.append(['name', component.name])
            table.append(['type', component.type.shortname])

            desc = textwrap.wrap(component.description, LIST_DESC_WIDTH)
            for i, line in enumerate(desc):
                table.append([
                    'description' if i == 0 else '',
                    line
                ])

            for i, dist in enumerate(component.dists):
                dist = component.dists[dist]
                table.append([
                    ('distributions'
                        if len(component.dists) > 1 else 'distribution')
                    if i == 0 else '',
                    '%s@%s' % (dist.name, dist.latest.version)
                ])

            if component.git is not None:
                table.append(['git', component.git])

            if component.manifest is not None:
                table.append(['manifest', component.manifest])

            table.append(['last checked', prettydate(component.last_checked)])

            localdir = component.localdir
            if os.path.isdir(localdir) and len(os.listdir(localdir)) != 0:
                table.append(['located at', localdir])

            for i, data in enumerate(table):
                table[i] = [
                    click.style(data[0] + ':' if len(data[0]) > 0 else '', fg="white"),
                    data[1]
                ]

            # print and remove last new line
            click.echo(pretty_columns(table)[:-1])
