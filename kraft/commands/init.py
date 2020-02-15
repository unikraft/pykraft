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
import platform
import kraft.util as util

from kraft.logger import logger
from kraft.project import Project
from kraft.errors import KraftError

from kraft.components import Core
from kraft.components import Platform
from kraft.components import Platforms
from kraft.components import Architecture
from kraft.components import Architectures
from kraft.types import RepositoryType

from kraft.commands.list import update
from kraft.util import ClickOptionMutex
from kraft.context import kraft_context

from kraft.constants import UNIKRAFT_CORE
from kraft.constants import KRAFTCONF_PREFERRED_PLATFORM
from kraft.constants import KRAFTCONF_PREFERRED_ARCHITECTURE

from kraft.config.interpolation import interpolate_source_version

@kraft_context
def kraft_init(ctx, name, target_plat, target_arch, template_app, version, force_create):
    """
    Initializes a new unikraft application.

    Start here if this is your first time using (uni)kraft.
    """

    # Pre-flight check determines if we are trying to work with nothing
    if ctx.cache.is_stale() and click.confirm('kraft caches are out-of-date.  Would you like to update?'):
        update()
    
    # Check if the directory is non-empty and prompt for validation
    if util.is_dir_empty(ctx.workdir) is False and force_create is False:
        if click.confirm('%s is a non-empty directory, would you like to continue?' % ctx.workdir):
            # It should be safe to set this now
            force_create = True
        else:
            logger.error('Cancelling!')
            sys.exit(1)
    
    # If we are using a template application, we can simply copy from the source
    # repository
    if template_app is not None:
    
        apps = {}

        for repo in ctx.cache.all():
            repo = ctx.cache.get(repo)

            if repo.type is RepositoryType.APP:
                apps[repo.name] = repo

        if template_app not in apps.keys():
            logger.error('Template application not found: %s' % template_app)
            logger.error('Supported templates: %s' % ', '.join(apps.keys()))
            sys.exit(1)
        
        app = apps[template_app]

        if version and version not in app.known_versions.keys():
            logger.error('Unknown version \'%s\' for app: %s' % (version, template_app))
            sys.exit(1)
        
        app.checkout(version)
        
        util.recursively_copy(app.localdir, ctx.workdir, overwrite=force_create, ignore=[
            '.git', 'build', '.config', '.config.old', '.config.orig'
        ])

        logger.info('Initialized new unikraft application \'%s\' in %s' % (name, ctx.workdir))
        
    
    # If no application is provided, we can initialize a template by dumping 
    # a YAML file
    else:
        # Determine the version of unikraft that we should be using
        if version is None:
            # This simply sets the "source" to the unikraft core repository which,
            # once parsed through the internal cache, should pop out the latest
            # version.
            unikraft_source = UNIKRAFT_CORE
            unikraft_version = None
        else:
            unikraft_source, unikraft_version = interpolate_source_version(
                source=version,
                repository_type=RepositoryType.CORE
            )

        try:
            core = Core.from_source_string(
                source=unikraft_source,
                version=unikraft_version
            )

            preferred_arch = ctx.settings.get(KRAFTCONF_PREFERRED_ARCHITECTURE)
            if target_arch is None:
                if preferred_arch:
                    target_arch = preferred_arch
                else:
                    logger.error("Please provide an architecture.")
                    sys.exit(1)
            
            arch_source, arch_version = interpolate_source_version(
                source=target_arch,
                repository_type=RepositoryType.ARCH
            )

            archs = Architectures([])
            archs.add(target_arch, Architecture.from_source_string(
                name = target_arch,
                source = arch_source,
            ), {})

            preferred_plat = ctx.settings.get(KRAFTCONF_PREFERRED_PLATFORM)
            if target_plat is None:
                if preferred_plat:
                    target_plat = preferred_plat
                else:
                    logger.error("Please provide a platform.")
                    sys.exit(1)
            
            plat_source, plat_version = interpolate_source_version(
                source=target_plat,
                repository_type=RepositoryType.PLAT
            )

            plats = Platforms([])
            plats.add(target_plat, Platform.from_source_string(
                name = target_plat,
                source = plat_source,
            ), {})

            logger.info("Using %s..." % core)

            project = Project(
                path=ctx.workdir,
                name=name,
                core=core,
                architectures=archs,
                platforms=plats,
            )

            project.init(
                force_create=force_create
            )
            logger.info('Initialized new unikraft application \'%s\' in %s' % (name, ctx.workdir))
        except KraftError as e:
            logger.error(str(e))
            sys.exit(1)

@click.command('init', short_help='Initialize a new unikraft application.')
@click.argument('name', required=True)
@click.option('--app', '-a', 'template_app', cls=ClickOptionMutex, not_required_if=['target_plat','target_arch'], help="Use an existing application as a template.")
@click.option('--plat', '-p', 'target_plat', cls=ClickOptionMutex, not_required_if=['template_app'], help='Target platform.', type=click.Choice(['linuxu', 'kvm', 'xen'], case_sensitive=True))
@click.option('--arch', '-m', 'target_arch', cls=ClickOptionMutex, not_required_if=['template_app'], help='Target architecture.', type=click.Choice(['x86_64', 'arm', 'arm64'], case_sensitive=True))
@click.option('--version', '-V', help="Use specific Unikraft release version.")
@click.option('--force', '-F', 'force_create', is_flag=True, help='Overwrite any existing files.')
def init(name, target_plat, target_arch, template_app, version, force_create):
    kraft_init(
        name=name,
        target_plat=target_plat,
        target_arch=target_arch,
        template_app=name,
        version=version,
        force_create=force_create
    )