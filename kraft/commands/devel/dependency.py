# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Gaulthier Gain <gaulthier.gain@uliege.be>
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
from kraft.utils import op, dir

import os
import subprocess

TOOLCHAIN_PATH = 'tools'
TOOLCHAIN_URL_GIT = 'https://github.com/gaulthiergain/tools.git'

def init_toolchain():
    """
    Set up the golang environment as well as the toolchain.
    """

    # Check if go is installed
    if not op.is_software_installed("go"):
        logger.debug("Go is not installed. Installing and setup.")
        op.execute_command("./scripts/install_go.sh")

    # Check if the toolchain is installed
    go_src_path = os.path.join(dir.get_home_dir(), 'go', 'src')
    toolchain_path = os.path.join(go_src_path, TOOLCHAIN_PATH)
    if not dir.existing_path(toolchain_path):
        os.chdir(go_src_path)
        op.execute_command('git', ['clone', TOOLCHAIN_URL_GIT])
    
    # Change to the toolchain repo
    os.chdir(toolchain_path)
    op.execute_command('git', ['checkout', 'staging'])
    op.execute_command('git', ['pull'])
    os.chdir(os.path.join(toolchain_path, 'srcs'))
    op.execute_command('make')

@click.command('dependency', short_help='Gather the dependencies of a specific application.', context_settings=dict(
    ignore_unknown_options=True, 
    allow_extra_args=True))  # noqa: C901
@click.pass_context
def dependency(ctx):
    """
    Gather the dependencies of a specific application.
    """
    
    try:
        # Init the toolchain environment
        init_toolchain()
        # Execute the toolchain with unparsed arguments 
        op.execute_command('./tools', ctx.args)
    
    except KraftError as e:
        logger.critical(e)
        sys.exit(1)
