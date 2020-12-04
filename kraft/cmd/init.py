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

import click

import kraft.util as util
from kraft.app import Application
from kraft.cmd.list import kraft_download_component
from kraft.cmd.list import kraft_list_preflight
from kraft.cmd.list import kraft_list_pull
from kraft.const import KRAFTRC_CONFIGURE_ARCHITECTURE
from kraft.const import KRAFTRC_CONFIGURE_PLATFORM
from kraft.const import UNIKRAFT_RELEASE_STABLE
from kraft.const import UNIKRAFT_WORKDIR
from kraft.error import UnknownApplicationTemplateName
from kraft.error import UnknownVersionError
from kraft.logger import logger
from kraft.types import ComponentType
from kraft.util import ClickOptionMutex


@click.pass_context
def kraft_app_init(ctx, appdir=None, name=None, plat=None, arch=None,
                   template_app=None, template_app_version=None,
                   force_init=False, pull_dependencies=False,
                   dumps_local=False, create_makefile=False):
    """

    """

    if appdir is None:
        raise ValueError("Cannot initialize application at unset directory")

    # If we are using a template application, we can simply copy from the source
    # repository
    if template_app is not None:
        app_manifest = None

        for manifest_origin in ctx.obj.cache.all():
            manifest = ctx.obj.cache.get(manifest_origin)

            for _, item in manifest.items():
                if item.name == template_app and item.type == ComponentType.APP:
                    app_manifest = item

        if app_manifest is None:
            raise UnknownApplicationTemplateName(template_app)

        version = None
        if template_app_version is not None:
            version = app_manifest.get_version(template_app_version)
            if version is None:
                raise UnknownVersionError(template_app_version, app_manifest)
        else:
            version = app_manifest.get_version(UNIKRAFT_RELEASE_STABLE)

        kraft_download_component(
            localdir=appdir,
            manifest=app_manifest,
            version=version.version
        )

        if pull_dependencies or dumps_local:
            workdir = None
            if dumps_local:
                workdir = os.path.join(appdir, UNIKRAFT_WORKDIR)

            kraft_list_pull(
                name=str(app_manifest),
                appdir=appdir,
                workdir=workdir,
                pull_dependencies=True,
                skip_app=True
            )

        logger.info('Initialized new unikraft application: %s' % appdir)

    # If no application is provided, we can initialize a template by dumping
    # a YAML file
    else:
        unikraft = ctx.obj.cache.find_item_by_name(
            type="core", name="unikraft"
        )

        unikraft.download()

        app = Application(
            name=name,
            unikraft=unikraft,
            architectures=[arch],
            platforms=[plat],
            localdir=appdir
        )

        app.init(
            create_makefile=create_makefile
        )


@click.command('init', short_help='Initialize a new unikraft application.')
@click.option(
    '--template', '-t', 'template_app',
    help='Use an existing application as a template.',
    cls=ClickOptionMutex, not_required_if=['plat', 'arch'],
    metavar="NAME"
)
@click.option(
    '--version', '-v', 'template_app_version',
    help='The version to use from the template application.',
    metavar="VERSION"
)
@click.option(
    '--plat', '-p', 'plat',
    help='Target platform.',
    cls=ClickOptionMutex,
    not_required_if=['template_app'],
    metavar="PLAT"
)
@click.option(
    '--arch', '-m', 'arch',
    help='Target architecture.',
    cls=ClickOptionMutex,
    not_required_if=['template_app'],
    metavar="ARCH"
)
@click.option(
    '--workdir', '-w', 'workdir',
    help='Specify an alternative directory for the application [default is cwd].',
    metavar="PATH"
)
@click.option(
    '--with-makefile', '-M', 'create_makefile',
    help='Create a Unikraft compatible Makefile.',
    is_flag=True
)
@click.option(
    '--no-deps', '-D', 'no_dependencies',
    help='Do not download additional dependencies for application components.',
    is_flag=True,
    cls=ClickOptionMutex,
    not_required_if=['dumps_local'],
)
@click.option(
    '--dump', '-d', 'dumps_local',
    help='Dump dependencies into project directory.',
    is_flag=True,
    cls=ClickOptionMutex,
    not_required_if=['no_dependencies'],
)
@click.option(
    '--force', '-F', 'force_init',
    help='Overwrite any existing files.',
    is_flag=True
)
@click.argument('name', required=False)
@click.pass_context
def cmd_init(ctx, name=None, plat=None, arch=None, template_app=None,
             template_app_version=None, workdir=None, create_makefile=False,
             no_dependencies=False, dumps_local=False, force_init=False):
    """
    Initializes a new unikraft application.

    Start here if this is your first time using (uni)kraft.
    """

    kraft_list_preflight()

    # kraft's init permutations:
    #
    # $ kraft                 init           => $(pwd)
    # $ kraft                 init my_app    => $(pwd)/my_app
    # $ kraft -w /path/to/app init           => /path/to/app
    # $ kraft -w /path/to/app init my_app    => /path/to/app/my_app

    if workdir is None and name is None:
        appdir = os.getcwd()
        name = os.path.basename(appdir)

    elif workdir is None:
        appdir = os.path.join(os.getcwd(), name)

    elif name is None:
        appdir = workdir
        name = os.path.basename(appdir)

    if arch is None:
        arch = ctx.obj.settings.get(KRAFTRC_CONFIGURE_ARCHITECTURE)

    if plat is None:
        plat = ctx.obj.settings.get(KRAFTRC_CONFIGURE_PLATFORM)

    # Check if the directory is non-empty and prompt for validation
    if util.is_dir_empty(appdir) is False and ctx.obj.assume_yes is False:
        if click.confirm('%s is a non-empty directory, would you like to continue?' % appdir):  # noqa: E501
            force_init = True
        else:
            logger.critical("Cannot create directory: %s" % appdir)
            sys.exit(1)

    try:
        kraft_app_init(
            name=name,
            appdir=appdir,
            plat=plat,
            arch=arch,
            template_app=template_app,
            template_app_version=template_app_version,
            create_makefile=create_makefile,
            force_init=force_init,
            pull_dependencies=not no_dependencies,
            dumps_local=dumps_local
        )
    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)
