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
import click
import datetime

from pathlib import Path
from git import Repo as GitRepo

from kraft.logger import logger

from kraft.component import Component
from kraft.component import ComponentManager

from kraft.const import MAKEFILE_UK
from kraft.const import TEMPLATE_LIB
from kraft.const import UK_VERSION_VARNAME
from kraft.const import UNIKRAFT_LIB_MAKEFILE_URL_EXT
from kraft.const import UNIKRAFT_LIB_MAKEFILE_VERSION_EXT

from cookiecutter.generate import generate_context
from cookiecutter.generate import generate_files
from cookiecutter.prompt import prompt_for_config
from cookiecutter.prompt import read_user_choice

from kraft.template import get_templates_path
from kraft.template import get_template_config
from kraft.template import delete_template_resources_of_disabled_features

from kraft.util import make_list_vars
from kraft.util import recursively_copy

from .provider import determine_lib_provider


def intrusively_determine_lib_origin(localdir=None, replace_var=True):
    """
    Intrusively determine the origin code's source URL if there is access to
    the Unikraft library directory.

    Args:
        localdir:  The local directory to read from.

    Returns
        origin url.
    """
    if localdir is None:
        raise ValueError("expected localdir")

    makefile_uk = os.path.join(localdir, MAKEFILE_UK)

    if os.path.exists(makefile_uk) is False:
        return

    makefile_vars = make_list_vars(makefile_uk)['makefile']

    lib_url_var = None
    lib_version_var = None

    for var in makefile_vars:
        if var.endswith(UNIKRAFT_LIB_MAKEFILE_URL_EXT):
            lib_url_var = var
            continue
        if var.endswith(UNIKRAFT_LIB_MAKEFILE_VERSION_EXT):
            lib_version_var = var
            continue

    if lib_version_var is not None:
        self.origin_version = makefile_vars[lib_version_var]
    else:
        return


class Library(Component):
    _origin_url = None
    @property
    def origin_url(self): return self._origin_url

    _origin_version = None
    @property
    def origin_version(self): return self._origin_version

    _origin_provider = None
    @property
    def origin_provider(self): return self._origin_provider

    _dependencies = None
    @property
    def dependencies(self): return self._dependencies

    _template_values = {}
    @property
    def template_value(self):
        return self._template_values

    @property
    def kname(self):
        name = self.name.upper()

        if name.startswith('LIB'):
            return name

        return 'LIB%s' % name

    @property
    def libname(self):
        name = self.name.lower()

        if name.startswith('lib-'):
            return name

        return 'lib-%s' % name

    @click.pass_context
    def __init__(ctx, self, *args, **kwargs):
        super(Library, self).__init__(*args, **kwargs)

        self._localdir = kwargs.get("localdir", None)
        self._origin_url = kwargs.get("origin_url", None)
        self._origin_version = kwargs.get("origin_version", None)
        self._template_value = dict()

        if self._origin_url is not None:
            self._origin_provider = determine_lib_provider(self._origin_url)

        # dependencies = kwargs.get("dependencies", None)

        self.set_template_value('year', datetime.datetime.now().year)
        self.set_template_value('project_name', self._name)
        self.set_template_value('version', self._origin_version)
        self.set_template_value('lib_name', self.libname)
        self.set_template_value('lib_kname', self.kname)
        self.set_template_value('commit', '')

    def set_template_value(self, key=None, val=None):
        if key is not None:
            self._template_values[key] = val

    @click.pass_context
    def init(ctx, self, extra_values=dict(), force_create=False,
            no_input=False):
        """
        """

        context = generate_context(
            context_file=get_template_config(TEMPLATE_LIB),
            default_context=self._template_values
        )

        # prompt the user to manually configure at the command line.
        # except when 'no-input' flag is set
        context['cookiecutter'] = prompt_for_config(context, no_input)

        self._description = context['cookiecutter']['description']
        self._template_values = dict(context['cookiecutter'])

        # Fix the starting "v" in the version string
        if context['cookiecutter']['version'].startswith('v'):
            context['cookiecutter']['version'] = context['cookiecutter']['version'][1:]
            context['cookiecutter']['source_archive'] = self.version_source_archive(
                'v%s' % (UK_VERSION_VARNAME % self.kname)
            )
        else:
            context['cookiecutter']['source_archive'] = self.version_source_archive()

        # include automatically generated content
        context['cookiecutter']['kconfig_dependencies'] = self.determine_kconfig_dependencies()
        context['cookiecutter']['source_files'] = self.determine_source_files()
        
        # include template dir or url in the context dict
        context['cookiecutter']['_template'] = get_templates_path(TEMPLATE_LIB)

        # add all vars that were never prompted
        for key in self._template_values:
            if key not in context['cookiecutter']:
                context['cookiecutter'][key] = self._template_values[key]

        
        output_dir = Path(self.localdir).parent
        # if self.source.startswith("file://"):
        #     output_dir = self.source[len("file://"):]

        logger.info("Generating files...")
        project_dir = generate_files(
            repo_dir=get_templates_path(TEMPLATE_LIB),
            context=context,
            overwrite_if_exists=force_create,
            skip_if_file_exists=not force_create,
            output_dir=output_dir,
        )

        delete_template_resources_of_disabled_features(self.localdir)

        # Save initial commit
        repo = GitRepo.init(self.localdir)
        repo.config_writer().set_value("user", "name", self.template_value['author_name']).release()
        repo.config_writer().set_value("user", "email", self.template_value['author_email']).release()
        repo.index.commit('Initial commit (blank)')

        logger.info("Generated new library: %s" % self.localdir)
        
    @click.pass_context
    def bump(ctx, self, version=None, fast_forward=False, force_version=False):
        """
        Change the Unikraft library's source origin version.  Usually this
        involves updating the LIBNAME_VERSION variable in the Makefile.uk file.

        Args:
            version:  The version to set.  If None, the latest version will be
                set.
            fast_forward:  If True, choose the latest version.
            force_version:  Whatever the specified version is, use it.

        Raises:
            NonCompatibleUnikraftLibrary:  Provided path is not a Unikraft
                library.
            UnknownLibraryOriginVersion:  The provided version does not match
                known versions from the origin.
            BumpLibraryDowngrade:  Attempting to downgrade a library.
            NoRemoteVersionsAvailable:  No remote versions to select from.
            CannotDetermineRemoteVersion:  Unable to determine which version to
                upgrade to.
            KraftError:  Miscellaneous error.
        """
        pass


    def version_source_archive(self, varname=None):
        """
        """

        if varname is None:
            varname = UK_VERSION_VARNAME % self.kname

        return self.origin_provider.version_source_archive(varname)

    # TODO: Intrusively determine which additional unikraft librareis are
    # needed for this library to run.
    def determine_kconfig_dependencies(self):
        return []

    # TODO: Intrusively determine source files of the origin for the library
    def determine_source_files(self):
        return []

class LibraryManager(ComponentManager):
    pass
