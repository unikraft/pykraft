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

import os
import click

from github import Github
from datetime import datetime

from kraft.context import kraft_context

from kraft.components import Repository
from kraft.errors import KraftError
from kraft.logger import logger

UK_GITHUB_ORG='unikraft'

@click.command('update', short_help='Update list of archs, platforms, libraries or applications.')
@kraft_context
def update(ctx):
    """
    This subcommand retrieves lists of available architectures, platforms,
    libraries and applications supported by unikraft.

    """

    if 'UK_KRAFT_GITHUB_TOKEN' in os.environ:
        github = Github(os.environ['UK_KRAFT_GITHUB_TOKEN'])
    else:
        github = Github()

    org = github.get_organization(UK_GITHUB_ORG)

    for repo in org.get_repos():
        # There is one repository which contains the codebase to kraft
        # itself (this code!) that is returned in this iteration.  Let's
        # filter it out here so we don't receive a prompt for an invalid
        # repository.
        if repo.clone_url == 'https://github.com/unikraft/kraft.git':
            continue

        try:
            logger.info("Found %s..." % repo.clone_url)
            Repository.from_source_string(
                source=repo.clone_url,
                force_update=True 
            )
        except KraftError as e:
            logger.error("Could not add repository: %s: %s" % (repo.clone_url, str(e)))
