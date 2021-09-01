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

import sys
from queue import Queue

import click
import six
from github.GithubException import RateLimitExceededException

from .provider.types import ListProviderType
from kraft.const import KRAFTRC_LIST_ORIGINS
from kraft.logger import logger
from kraft.manifest import Manifest


@click.command('update', short_help='Update the list of remote components.')
@click.pass_context
def cmd_list_update(ctx):
    """
    Update the list of known Unikraft components.  This will search for
    repositories specified in the origins section of your ~/.kraftrc file.
    """
    kraft_update()


@click.pass_context  # noqa: C901
def kraft_update(ctx, origins=list()):
    if isinstance(origins, six.string_types):
        origins = [origins]

    if len(origins) == 0:
        origins = ctx.obj.settings.get(KRAFTRC_LIST_ORIGINS)

    if origins is None or len(origins) == 0:
        logger.error("No source origins available.  Please see: kraft list add --help")
        sys.exit(1)

    try:
        for origin in origins:
            manifest = ctx.obj.cache.get(origin)

            if manifest is None:
                manifest = Manifest(
                    manifest=origin
                )

            threads, items = kraft_update_from_source_threads(origin)

            for thread in threads:
                thread.join()

            # Check thread's return value
            while not items.empty():
                result = items.get()
                if result is not None:
                    manifest.add_item(result)
                    logger.info(
                        "Found %s/%s via %s..." % (
                            click.style(result.type.shortname, fg="blue"),
                            click.style(result.name, fg="blue"),
                            manifest.manifest
                        )
                    )
                    ctx.obj.cache.save(origin, manifest)

    except RateLimitExceededException:
        for line in [
            "GitHub rate limit exceeded!  If you have not done so already,",
            "you can tell kraft to use a personal access token when contacting",
            "the GitHub API.  First, visit:",
            "",
            "  https://github.com/settings/tokens/new",
            "",
            "then select 'repo:public_repo'.  You can then set the",
            "environmental variable UK_KRAFT_GITHUB_TOKEN with this new token,",
            "for example:",
            "",
            "  export UK_KRAFT_GITHUB_TOKEN=<token>",
            "",
            "Once this is done, please try again :-)"
        ]:
            logger.error(line)

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)

    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)


@click.pass_context
def kraft_update_from_source_threads(ctx, origin=None):
    threads = list()
    items = Queue()

    for _, provider in ListProviderType.__members__.items():
        if provider.is_type(origin):
            provider = provider.cls()
            with ctx:
                extra_items, extra_threads = provider.probe(
                    origin=origin,
                    items=items,
                    return_threads=True
                )
            if extra_threads is not None and isinstance(extra_threads, list):
                threads.extend(extra_threads)

            break

    return threads, items


@click.pass_context
def kraft_update_from_source(ctx, origin=None):
    manifest = None

    for _, provider in ListProviderType.__members__.items():
        if provider.is_type(origin):
            provider = provider.cls()
            manifest = provider.probe(origin=origin)
            break

    return manifest
