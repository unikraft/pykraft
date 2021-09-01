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
from urllib.parse import urlparse

import click

from kraft.cmd.list.update import kraft_update
from kraft.const import KRAFTRC_LIST_ORIGINS
from kraft.logger import logger


@click.pass_context
def kraft_list_add(ctx, origin=None, update=False):
    """
    """
    if isinstance(origin, list):
        for o in origin:
            kraft_list_add(o, update=update)
        return

    existing_origins = ctx.obj.settings.get(KRAFTRC_LIST_ORIGINS)
    if existing_origins is None:
        existing_origins = list()

    new_uri = urlparse(origin)

    if os.path.exists(origin):
        origin = os.path.abspath(origin)

    for o in existing_origins:
        cur_uri = urlparse(o)
        if (o == origin
                or (new_uri.netloc == cur_uri.netloc
                    and new_uri.path == cur_uri.path)):
            logger.warning("Origin already saved: %s" % o)
            return

    existing_origins.append(origin)
    ctx.obj.settings.set(KRAFTRC_LIST_ORIGINS, existing_origins)
    logger.info("Saved: %s" % origin)

    if update:
        with ctx:
            kraft_update(origin)


@click.command('add', short_help='Add a remote manifest or repository.')
@click.option(
    '--update/--no-update', 'update',
    help='Update the list of known remote components.',
    default=False
)
@click.argument('origin', nargs=-1)
@click.pass_context
def cmd_list_add(ctx, update=False, origin=None):
    """
    Add a remote repository to search for components.
    """

    try:
        kraft_list_add(list(origin), update=update)

    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)
