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
import fileinput
import os
import shutil
import urllib.request

import kconfiglib
import semver
import yaml
from cookiecutter.generate import generate_context
from cookiecutter.generate import generate_files
from cookiecutter.prompt import prompt_for_config
from cookiecutter.prompt import read_user_choice
from git import Repo as GitRepo
from kconfiglib import KconfigError

from kraft.components.provider import determine_provider
from kraft.components.repository import Repository
from kraft.components.repository import RepositoryManager
from kraft.components.types import RepositoryType
from kraft.constants import CONFIG_UK
from kraft.constants import MAKEFILE_UK
from kraft.constants import SEMVER_PATTERN
from kraft.constants import TEMPLATE_CONFIG
from kraft.constants import TEMPLATE_MANIFEST
from kraft.constants import UK_VERSION_VARNAME
from kraft.constants import UNIKRAFT_LIB_KNOWN_MAKEFILE_VAR_EXTS
from kraft.constants import UNIKRAFT_LIB_MAKEFILE_URL_EXT
from kraft.constants import UNIKRAFT_LIB_MAKEFILE_VERSION_EXT
from kraft.constants import VSEMVER_PATTERN
from kraft.context import kraft_context
from kraft.errors import BumpLibraryDowngrade
from kraft.errors import CannotConnectURLError
from kraft.errors import CannotDetermineRemoteVersion
from kraft.errors import NonCompatibleUnikraftLibrary
from kraft.errors import NoRemoteVersionsAvailable
from kraft.errors import UnknownLibraryOriginVersion
from kraft.errors import UnknownSourceProvider
from kraft.logger import logger
from kraft.utils import delete_resource
from kraft.utils import is_dir_empty
from kraft.utils import make_list_vars
from kraft.utils import recursively_copy


def get_templates_path():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '../templates'
    )


def get_template_config():
    return os.path.join(
        get_templates_path(),
        TEMPLATE_CONFIG
    )


def delete_resources_for_disabled_features(templatedir=None):
    if templatedir is None:
        return

    template_manifest = os.path.join(templatedir, TEMPLATE_MANIFEST)

    if os.path.exists(template_manifest) is False:
        return

    with open(template_manifest) as manifest_file:
        manifest = yaml.load(manifest_file, Loader=yaml.FullLoader)

        for feature in manifest['features']:
            if not feature['enabled']:
                for resource in feature['resources']:
                    delete_resource(os.path.join(templatedir, resource))

    delete_resource(template_manifest)


def library_check_integrity(path=None):
    if path is None:
        return False

    if is_dir_empty(path):
        return False

    config_uk = os.path.join(path, CONFIG_UK)
    logger.debug("Checking %s..." % config_uk)

    if os.path.exists(config_uk) is False:
        return False

    try:
        kconfiglib.Kconfig(
            filename=config_uk,
            warn_to_stderr=False,
        )

    except KconfigError as e:
        logger.warning(e)
        return False

    makefile_uk = os.path.join(path, MAKEFILE_UK)
    logger.debug("Checking %s..." % makefile_uk)

    if os.path.exists(makefile_uk) is False:
        return False

    makefile_vars = make_list_vars(makefile_uk)['makefile']

    # Set a variable of known variable extensions such that we can pop from it
    # as we discover them in a provided Makefile.uk file.
    known_vars = UNIKRAFT_LIB_KNOWN_MAKEFILE_VAR_EXTS

    for var in makefile_vars:
        for known_var in known_vars:
            if var.endswith(known_var):
                known_vars.remove(known_var)
                continue  # skip to next makefile variable

    if len(known_vars) == 0:
        return True

    return False


def does_version_start_with_v():
    pass


class Library(Repository):
    _origin_source = None
    _origin_provider = None
    _template_values = {}

    @classmethod
    def from_config(cls, ctx, name, config=None, save_cache=True):
        assert ctx is not None, "ctx is undefined"

        source = None
        version = None

        if 'source' in config:
            source = config['source']

        if 'version' in config:
            version = config['version']

        return super(Library, cls).from_unikraft_origin(
            name=name,
            source=source,
            version=version,
            repository_type=RepositoryType.LIB,
            save_cache=save_cache,
        )

    @classmethod
    def from_unikraft_origin(cls, name, source, localdir=None, save_cache=True):
        library = super(Library, cls).from_unikraft_origin(
            name=name,
            source=source,
            repository_type=RepositoryType.LIB,
            localdir=localdir,
            save_cache=save_cache,
        )

        library.intrusively_determine_origin()

        return library

    @classmethod
    def from_source_origin(cls,
                           name=None,
                           origin=None,
                           source=None,
                           version=None,
                           save_cache=False):
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
    def origin_source(self, use_var=False):
        if use_var:
            pass
        # # Replace $(...) format with the actual version
        # libname = lib_url_var.replace(UNIKRAFT_LIB_MAKEFILE_URL_EXT, '')
        # varname = UK_VERSION_VARNAME % libname
        # self.origin_source = makefile_vars[lib_url_var].replace(varname, self.origin_version)
        # self.origin_provider = determine_provider(self.origin_source)

        return self._origin_source

    @origin_source.setter
    def origin_source(self, origin_source=None):
        self._origin_source = origin_source

    @property
    def origin_provider(self):
        return self._origin_provider

    @origin_provider.setter
    def origin_provider(self, origin_provider=None):
        self._origin_provider = origin_provider

    def intrusively_determine_origin(self, localdir=None, replace_var=True):
        """
        Intrusively determine the origin code's source URL if there is access to
        the Unikraft library directory.

        Args:
            localdir:  The local directory to read from.

        Returns
            origin url.
        """
        if localdir is None:
            localdir = self.localdir

        if localdir is None:
            return

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

        if lib_url_var is not None:
            self.origin_source = makefile_vars[lib_url_var]
            self.origin_provider = determine_provider(self.origin_source)

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
        """
        """

        if varname is None:
            varname = UK_VERSION_VARNAME % self.kname

        return self.provider.version_source_archive(varname)

    @classmethod
    def check_integrity(cls, path=None):
        return library_check_integrity(path)

    @property
    def origin_version(self):
        return self._origin_version

    @origin_version.setter
    def origin_version(self, version=None):
        self._origin_version = version

    @kraft_context  # noqa: C901
    def bump(ctx,
             self,
             version=None,
             fast_forward=False,
             force_version=False):
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

        # if path is None:
        #     raise NonCompatibleUnikraftLibrary(path)

        # name = os.path.basename(path)

        # library = Library.from_unikraft_origin(
        #     name=name,
        #     source=path,
        #     localdir=path,
        #     save_cache=False,
        # )

        # if checkout:
        #     print('checking out')
        #     library.checkout()

        # Check if the directory is a library
        if library_check_integrity(self.localdir) is False:
            raise NonCompatibleUnikraftLibrary(self.localdir)

        # Retrieve known versions
        versions = self.origin_provider.probe_remote_versions()

        semversions = []

        if len(versions) == 0:
            raise NoRemoteVersionsAvailable(self.origin_source)

        # filter out non-semver versions
        for known_version in list(versions.keys()):
            found = SEMVER_PATTERN.search(known_version)

            if found is not None:
                semversions.append(known_version)

        current_version = self.origin_version

        if version is None:

            # Pick the highest listed verson
            if ctx.assume_yes:

                # There are no semversions
                if len(semversions) == 0:
                    raise CannotDetermineRemoteVersion(self.localdir)

                latest_version = sorted(semversions, reverse=True)[0]

                current_not_semver = False

                try:
                    semver.VersionInfo.parse(current_version)
                except ValueError as e:
                    logger.warn(e)
                    current_not_semver = True

                # Pick the latest version
                if fast_forward or current_not_semver:
                    version = latest_version

                # Check if we're already at the latest version
                elif semver.compare(current_version, latest_version) == 0:
                    version = latest_version

                # Find the next version
                else:
                    semversions = sorted(semversions)

                    for i in range(len(semversions)):
                        if semver.compare(semversions[i], current_version) == 0:
                            # We should have never made it this far, but because we
                            # did, we're at the latest version.
                            if i + 1 == len(semversions):
                                version = latest_version
                                break

                            # Select the next version
                            else:
                                version = semversions[i + 1]
                                break

            # Prompt user for a version
            else:
                version = read_user_choice('version', sorted(list(versions.keys()), reverse=True))

        if version not in versions.keys():
            if ctx.assume_yes:
                logger.warn(
                    "Provided version '%s' not known in: {%s}"
                    % (version, ', '.join(versions.keys()))
                )
            else:
                raise UnknownLibraryOriginVersion(version, versions.keys())

        if VSEMVER_PATTERN.search(version):
            version = version[1:]

        # Are we dealing with a semver pattern?
        try:
            if semver.compare(current_version, version) == 0:
                logger.info("Library already latest version: %s" % version)
                return version

            if semver.compare(current_version, version) > 0:
                if force_version:
                    logger.warn(
                        "Downgrading library from %s to %s..."
                        % (current_version, version)
                    )
                else:
                    raise BumpLibraryDowngrade(current_version, version)

        except ValueError:
            if current_version == version:
                logger.info("Library already at version: %s" % version)
                return version

        # Actually perform the bump
        makefile_uk = os.path.join(self.localdir, MAKEFILE_UK)
        logger.debug("Reading %s..." % makefile_uk)

        makefile_vars = make_list_vars(makefile_uk)['makefile']
        version_var = None

        for var in makefile_vars:
            if var.endswith(UNIKRAFT_LIB_MAKEFILE_VERSION_EXT):
                version_var = var
                break

        logger.info('Upgrading library from %s to %s...' % (current_version, version))

        for line in fileinput.input(makefile_uk, inplace=1):
            if line.startswith(version_var) and current_version in line:
                print('%s = %s' % (version_var, version))
            else:
                print(line, end='')

        return version


class Libraries(RepositoryManager):
    pass
