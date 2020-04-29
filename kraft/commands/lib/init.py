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
import sys
import click

from git import GitConfigParser
from configparser import NoOptionError

import kraft.utils as utils
from kraft.logger import logger
from kraft.kraft import kraft_context
from kraft.components.library import Library

from kraft.errors import UnknownSourceProvider
from kraft.errors import CannotConnectURLError

from kraft.constants import URL_VERSION
from kraft.constants import GITCONFIG_LOCAL
from kraft.constants import GITCONFIG_GLOBAL

@click.command('init', short_help='Initialize a new Unikraft library.')
@click.argument('name', required=False)
@click.option('--author-name',  '-a', 'author_name',    help='The author\'s name for library.')
@click.option('--author-email', '-e', 'author_email',   help='The author\'s email for library.')
@click.option('--github',       '-g', 'from_github',    help='The remote repository is from GitHub.', is_flag=True)
@click.option('--version',      '-v', 'version',        help='Set the version to use from GitHub.')
@click.option('--origin',       '-s', 'origin',         help='Source code origin URL.  Use the semantic %s for automatic versioning.' % URL_VERSION)
@click.option('--provide-main', '-m', 'provide_main',   help='Provide a main function override.', is_flag=True)
@click.option('--dependencies', '-d', 'dependencies',   help='Select known library dependencies', multiple=True)
@click.option('--force',        '-F', 'force_create',   help='Overwrite any existing files.', is_flag=True)
@click.option('--no-input',     '-A', 'no_input',       help='Do not prompt the user at command line configuration', is_flag=True)
@kraft_context
def init(ctx, name, author_name, author_email, from_github, version, origin, provide_main, dependencies, force_create, no_input):
    """Initialize a new Unikraft library."""

    libdir = ctx.workdir

    if name is None:
        name = os.path.basename(os.getcwd())
    
    else:
        libdir = os.path.join(libdir, name)

    if os.path.exists(libdir) is False:
        os.mkdir(libdir)

    # Check if the directory is non-empty and prompt for validation
    if utils.is_dir_empty(libdir) is False and force_create is False:
        if click.confirm('%s is a non-empty directory, would you like to continue?' % libdir):
            # It should be safe to set this now
            force_create = True
        
        else:
            logger.fatal('Cancelling!')
            sys.exit(1)

    gitconfig = None

    if author_name is None or author_email is None:
        # Attempt reading author and email from .git/config
        if os.path.exists(os.path.join(libdir, '.git')):
            gitconfig = GitConfigParser(
                [os.path.normpath(os.path.join(libdir, GITCONFIG_LOCAL))],
                read_only=True
            )
    
        # Attempt reading default author and email from ~/.gitconfig
        else:
            gitconfig = GitConfigParser(
                [os.path.normpath(os.path.expanduser(GITCONFIG_GLOBAL))],
                read_only=True
            )

    try:
        if author_name is None:
            author_name = gitconfig.get("user", "name")
        
        if author_email is None:
            author_email = gitconfig.get("user", "email")
        
    except NoOptionError:
        pass

    if origin is None:
        origin = click.prompt("source (Use %s for automatic versioning)" % URL_VERSION)

    try:
        library = Library.from_origin(
            name = name,
            origin = origin,
            source = libdir,
            version = version,
        )
    
    except (UnknownSourceProvider, CannotConnectURLError) as e:
        logger.fatal(e)
        sys.exit(1)

    library.set_template_value('author_name', author_name)
    library.set_template_value('author_email', author_email)
    library.set_template_value('provide_main', provide_main)

    if dependencies is not None:
        library.set_template_value('kconfig_dependencies', dependencies)
    
    library.save(
        outdir=libdir,
        no_input=no_input,
        force_create=force_create,
    )