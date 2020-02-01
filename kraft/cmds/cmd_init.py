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

import os
import sys
import click
import platform
import kraft.util as util
from kraft.logger import logger
from kraft.env import pass_environment
from kraft.component import KraftComponent
from kraft.app import UnikraftApp, IncompatibleKConfig, NonExistentLibrary, MisconfiguredUnikraftApp

@click.command('init', short_help='Initialize a new unikraft project.')
@click.argument('path', required=False, type=click.Path(resolve_path=True))
@click.argument('name', required=False)
@click.option('--arch', '-m', help='Target architecture', default=lambda:platform.machine(), show_default=True)
@click.option('--plat', '-p', default='linuxu', help='Target platform', show_default=True)
@click.option('--lib', '-l', multiple=True, help='Target platform')
@click.option('--app', '-a', help='Use existing application')
@click.option('--force', '-F', is_flag=True, help='Overwrite any existing files.')
# @click.option('--dry-run', '-T', is_flag=True, help='Predict the creation of a repository.')
# @click.option('--no-cache', '-X', is_flag=True, help='Don\'t use local cache and download everything .')
@pass_environment
def cli(ctx, path, name, arch, plat, lib, app, force):
    """
    This subcommand initializes a new unikraft application at a selected path.

    Start here if this is your first time using (uni)kraft.
    """

    # Pre-flight check determines if we are trying to work with nothing
    if ctx.cache.is_stale():
        if click.confirm('kraft caches are out-of-date, would you like to update?'):
            ctx.cache.update()

    if path is None:
        path = os.getcwd()

    # Check if the directory is non-empty and prompt for validation
    if util.is_dir_empty(path) is False and force is False:
        if click.confirm('%s is a non-empty directory, would you like to continue?' % path):
            # It should be safe to set this now
            force = True
        else:
            click.echo('Cancelling!')
            sys.exit(1)
    
    # Set the current known version for core, arch and plat
    core = ctx.cache.repos(KraftComponent.CORE)['unikraft']
    core = (core, core.release)
    
    archs = ctx.cache.repos_names(KraftComponent.ARCH)
    if arch not in archs:
        click.echo("Unsupported architecture: %s (choices: %s)" % (arch, archs))
        sys.exit(1)
    else:
        arch = ctx.cache.repos(KraftComponent.ARCH)[arch]
        arch = (arch, arch.release)

    plats = ctx.cache.repos_names(KraftComponent.PLAT)
    if plat not in plats:
        click.echo("Unsupported platform: %s (choices: %s)" % (plat, plats))
        sys.exit(1)
    else:
        plat = ctx.cache.repos(KraftComponent.PLAT)[plat]
        plat = (plat, plat.release)

    use_template = None
    if app is not None:
        apps = ctx.cache.repos_names(KraftComponent.APP)
        if app not in apps:
            click.echo("Unsupported application: %s (choices: %s)" % (app, apps))
            sys.exit(1)
        else:
            use_template = ctx.cache.repos(KraftComponent.APP)[app]

    if name is None:
        name = click.prompt('Name of new unikraft project')

    try:
        app = UnikraftApp(
            ctx=ctx,
            name=name,
            core=core,
            path=path,
            arch=arch,
            plat=plat,
            use_template=use_template,
            # no_cache=no_cache,
        )
    except MisconfiguredUnikraftApp as e:
        click.echo("Unsupported configuration: %s" % str(e))
        sys.exit(1)

    for l in list(lib):
        try:
            app.add_lib(l)
        except NonExistentLibrary as e:
            click.echo("Non-existent library: %s" % str(e))
            sys.exit(1)

    app.save(force_overwrite=force)

    # Everything has worked out in the end
    click.echo('Initialized new unikraft application \'%s\' in %s' % (name, path))
    click.echo(str(app))
