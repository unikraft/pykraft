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
from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import os
import shutil
import urllib.request

import yaml
from cookiecutter.generate import generate_context
from cookiecutter.generate import generate_files
from cookiecutter.prompt import prompt_for_config
from git import Repo as GitRepo

from kraft.components.provider import determine_provider
from kraft.components.repository import Repository
from kraft.components.repository import RepositoryManager
from kraft.components.types import RepositoryType
from kraft.constants import PROJECT_CONFIG
from kraft.constants import PROJECT_MANIFEST
from kraft.constants import UK_VERSION_VARNAME
from kraft.errors import CannotConnectURLError
from kraft.errors import UnknownSourceProvider
from kraft.logger import logger
from kraft.utils import delete_resource
from kraft.utils import recursively_copy


def get_templates_path():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '../templates'
    )


def get_template_config():
    return os.path.join(
        get_templates_path(),
        PROJECT_CONFIG
    )


def delete_resources_for_disabled_features(project_dir=None):
    if project_dir is None:
        return

    project_manifest = os.path.join(project_dir, PROJECT_MANIFEST)

    if os.path.exists(project_manifest) is False:
        return

    with open(project_manifest) as manifest_file:
        manifest = yaml.load(manifest_file, Loader=yaml.FullLoader)

        for feature in manifest['features']:
            if not feature['enabled']:
                for resource in feature['resources']:
                    delete_resource(os.path.join(project_dir, resource))

    delete_resource(project_manifest)


class Library(Repository):
    _origin = None
    _template_values = {}

    @classmethod
    def from_config(cls, ctx, name, config=None):
        assert ctx is not None, "ctx is undefined"

        source = None
        version = None

        if 'source' in config:
            source = config['source']

        if 'version' in config:
            version = config['version']

        return super(Library, cls).from_source_string(
            name=name,
            source=source,
            version=version,
            repository_type=RepositoryType.LIB
        )

    @classmethod
    def from_source_string(cls, name, source):
        return super(Library, cls).from_source_string(
            name=name,
            source=source,
            repository_type=RepositoryType.LIB
        )

    @classmethod
    def from_origin(cls,
                    name=None,
                    origin=None,
                    source=None,
                    version=None):
        """"""

        try:
            logger.debug("Pinging %s..." % origin)
            urllib.request.urlopen(origin).getcode()

        except OSError as e:
            raise CannotConnectURLError(origin, e.msg)

        if os.path.exists(os.path.join(source, '.git')) is False:
            logger.debug("Initializing new git repository at: %s" % source)
            GitRepo.init(source)

        provider = determine_provider(origin)

        if provider is None:
            raise UnknownSourceProvider(source)

        # Initialize the "repository"
        library = cls(
            name=name,
            source="file://%s" % source,
            repository_type=RepositoryType.LIB,
            provider=provider,
            version=version,
        )

        library.origin = origin
        versions = library.provider.probe_remote_versions()
        library.set_template_value('version', sorted(list(versions.keys()), reverse=True))
        library.set_template_value('year', datetime.datetime.now().year)
        library.set_template_value('project_name', name)
        library.set_template_value('library_name', library.libname)
        library.set_template_value('library_kname', library.kname)
        library.set_template_value('commit', '')

        return library

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, origin=None):
        self._origin = origin

    def save(self,
             outdir=None,
             additional_values={},
             force_create=False,
             no_input=False):
        context = generate_context(
            context_file=get_template_config(),
            default_context=self._template_values
        )

        # prompt the user to manually configure at the command line.
        # except when 'no-input' flag is set
        context['cookiecutter'] = prompt_for_config(context, no_input)

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
        context['cookiecutter']['_template'] = get_templates_path()

        # add all vars that were never prompted
        for key in self._template_values:
            if key not in context['cookiecutter']:
                context['cookiecutter'][key] = self._template_values[key]

        output_dir = self.source
        if self.source.startswith("file://"):
            output_dir = self.source[len("file://"):]

        logger.info("Generating files...")
        project_dir = generate_files(
            repo_dir=get_templates_path(),
            context=context,
            overwrite_if_exists=force_create,
            skip_if_file_exists=not force_create,
            output_dir=outdir,
        )

        recursively_copy(project_dir, outdir, overwrite=force_create)
        delete_resources_for_disabled_features(outdir)
        shutil.rmtree(project_dir, ignore_errors=True)

        # Save initial commit
        repo = GitRepo(output_dir)
        repo.config_writer().set_value("user", "name", self.template_value['author_name']).release()
        repo.config_writer().set_value("user", "email", self.template_value['author_email']).release()
        repo.index.commit('Initial commit (blank)')

    def set_template_value(self, key=None, val=None):
        if key is not None:
            self._template_values[key] = val

    @property
    def template_value(self):
        return self._template_values

    # TODO: Intrusively determine which additional unikraft librareis are
    # needed for this library to run.
    def determine_kconfig_dependencies(self):
        return []

    # TODO: Intrusively determine source files of the origin for the library
    def determine_source_files(self):
        return []

    def version_source_archive(self, varname=None):
        if varname is None:
            varname = UK_VERSION_VARNAME % self.kname

        return self.provider.version_source_archive(varname)


class Libraries(RepositoryManager):
    pass
