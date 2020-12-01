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
import json
import time
import click
import semver
import threading

from pathlib import Path
from atpbar import flush

from kraft.app import Application
from kraft.util import pretty_columns
from kraft.util import prettydate
from kraft.util import ErrorPropagatingThread
from kraft.logger import logger
from kraft.error import UnknownVersionError
from kraft.error import KraftError
from kraft.const import UNIKRAFT_RELEASE_STABLE
from kraft.manifest import ManifestItem
from kraft.types import break_component_naming_format
from kraft.types import str_to_component_type
from kraft.types import ComponentType
from kraft.manifest import ManifestVersionEquality

from .list import kraft_list_preflight


@click.pass_context
def kraft_list_pull(ctx, name=None, workdir=None, use_git=False,
        pull_dependencies=False, skip_verify=False, appdir=None,
        skip_app=False):
    """
    Pull a particular component from a known manifest.  This will retrieve
    the contents to either the automatically determined directory or to an
    alternative working directory.

    Args:
        name (str):  The name of the component(s) to pull.  This can be the full
            qualifier, e.g.: lib/python3==0.4, partial, or the minimum: python3.
        workdir (str):  The path to save the component(s).
        use_git (bool):  Whether to use git to retrieve the components.
        pull_dependencies (bool):  If an application is specified in name, this
            will signal to pull the listed libraries for this.
        appdir (str):  Used in conjunction with pull_dependencies and used to
            specify the application from which the dependencies are determined
            and then pulled.
    """

    manifests = list()
    names = list()
    if isinstance(name, tuple):
        names = list(name)
    elif name is not None:
        names.append(name)
    
    not_found = list()
    if isinstance(name, tuple):
        not_found = list(name)
    elif name is not None:
        not_found.append(name)
    
    # Pull the dependencies for the application at workdir or cwd
    if pull_dependencies and (len(names) == 0 or \
        appdir is not None and len(names) == 1):
        app = Application.from_workdir(
            appdir if appdir is not None
            else workdir if workdir is not None
            else os.getcwd()
        )
        for component in app.components:
            if component.manifest is not None:
                manifests.append((
                    component.manifest,
                    ManifestVersionEquality.EQ,
                    component.version.version
                ))
        
    # Pull the provided named components
    else:
        for manifest_origin in ctx.obj.cache.all():
            manifest = ctx.obj.cache.get(manifest_origin)

            for _, manifest in manifest.items():
                if len(names) == 0:
                    manifests.append((manifest, 0, None))
            
                else:
                    for fullname in names:
                        type, name, eq, version = \
                            break_component_naming_format(fullname)

                        if (type is None or \
                                (type is not None \
                                    and type.shortname == manifest.type)) \
                                and manifest.name == name:
                            manifests.append((manifest, eq, version))

                            # Accomodate for multi-type names
                            if fullname in not_found:
                                not_found.remove(fullname)

    for name in not_found:
        logger.warn("Could not find manifest: %s" % name)

    if len(manifests) == 0:
        logger.error("No manifests to download")
        sys.exit(1)
    
    for manifest in manifests:
        if skip_app and manifest[0].type == ComponentType.APP:
            continue

        kraft_download_via_manifest(
            workdir=workdir,
            manifest=manifest[0],
            equality=manifest[1],
            version=manifest[2],
            use_git=use_git,
            skip_verify=skip_verify
        )
    
    if pull_dependencies and len(names) > 0:
        for manifest in manifests:
            if manifest[0].type == ComponentType.APP.shortname:
                kraft_list_pull(
                    appdir=appdir,
                    workdir=workdir,
                    use_git=use_git,
                    pull_dependencies=True,
                    skip_verify=skip_verify
                )

@click.pass_context
def kraft_download_via_manifest(ctx, workdir=None, manifest=None, 
        equality=None, version=None, use_git=False, skip_verify=False):
    """
    """
    threads = list()

    def kraft_download_component_thread(localdir=None, manifest=None,
        equality=ManifestVersionEquality.EQ, version=None, use_git=False,
        skip_verify=False, override_existing=False):
        with ctx:
            kraft_download_component(localdir=localdir, manifest=manifest,
                equality=equality, version=version, use_git=use_git,
                skip_verify=skip_verify, 
                override_existing=override_existing)

    if workdir is None:
        localdir = manifest.localdir
    elif manifest.type == ComponentType.CORE:
        localdir = os.path.join(workdir, manifest.type.workdir)
    else:
        localdir = os.path.join(workdir, manifest.type.workdir, manifest.name)

    thread = ErrorPropagatingThread(
        target=kraft_download_component_thread,
        kwargs={
            'localdir': localdir,
            'manifest': manifest,
            'equality': equality,
            'version': version,
            'use_git': use_git,
            'skip_verify': skip_verify
        }
    )
    threads.append((manifest, thread))
    thread.start()

    for manifest, thread in threads:
        try:
            thread.join()
        except Exception as e:
            logger.error("Error pulling manifest: %s " % e)

            if ctx.obj.verbose:
                import traceback
                logger.error(traceback.format_exc())
    
    if sys.stdout.isatty():
        flush()


@click.pass_context
def kraft_download_component(ctx, localdir=None, manifest=None,
        equality=ManifestVersionEquality.EQ, version=None, use_git=False,
        skip_verify=False, override_existing=False):
    """
    """
    if manifest is None or not isinstance(manifest, ManifestItem):
        raise TypeError("expected ManifestItem")

    path = Path(localdir)
    if not os.path.exists(str(path.parent)):
        os.makedirs(str(path.parent), exist_ok=True)

    with ctx:
        manifest.download(
            localdir=localdir,
            equality=equality,
            version=version,
            override_existing=override_existing,
            use_git=use_git,
        )


@click.command('pull', short_help='Pull the remote component to disk.')
@click.option(
    '--workdir', '-w', 'workdir',
    help='Save the component to an alternative working directory.',
    metavar="PATH"
)
@click.option(
    '--git', '-g', 'use_git',
    help='Download the manifest via a git pull.',
    is_flag=True
)
@click.option(
    '--no-deps', '-D', 'no_dependencies',
    help='Do not download additional dependencies for application components.',
    is_flag=True
)
@click.option(
    '--skip-verify', '-k', 'skip_verify',
    help='Skip the verification of the manifest.',
    is_flag=True
)
@click.argument('name', required=False, nargs=-1)
@click.pass_context
def cmd_list_pull(ctx, name=None, workdir=None, use_git=False,
        no_dependencies=False, skip_verify=False):
    """
    Download a remote component to your working directory.

    You can additional syntax to specify the type of component and/or the 
    version you wish to download.  The name of a component is specified by
    either its unique name or by its type and name (e.g. [type]/[name] or
    [type]-[name]).  The version can be specified using an equality operator:
    at the specific version/distribution (e.g. [name]==[version]) or equal and
    above the specific version (e.g. [name]>=[version]).

    To pull an application and its depedencies, simply call the specified name:

        $ kraft list pull python3

        $ kraft list pull app-python3

        $ kraft list pull app/python3
    
    To simply pull a library:

        $ kraft list pull lib-python3

        $ kraft list pull lib/python3
    
    To pull a component at a specific version:

        $ kraft list pull lib/python3==stable

        $ kraft list pull lib-python3>=0.4

    """

    kraft_list_preflight()

    try:
        kraft_list_pull(
            name=name, 
            workdir=workdir, 
            use_git=use_git, 
            pull_dependencies=not no_dependencies,
            skip_verify=skip_verify
        )
    
    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)
