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

import datetime
import fileinput
import os
from pathlib import Path

import click
import semver
from cookiecutter.generate import generate_context
from cookiecutter.generate import generate_files
from cookiecutter.prompt import prompt_for_config
from cookiecutter.prompt import read_user_choice
from git import Repo as GitRepo

from .provider import determine_lib_provider
from kraft.component import Component
from kraft.component import ComponentManager
from kraft.const import MAKEFILE_UK
from kraft.const import SEMVER_PATTERN
from kraft.const import TEMPLATE_LIB
from kraft.const import UK_VERSION_VARNAME
from kraft.const import UNIKRAFT_BUILDDIR
from kraft.const import UNIKRAFT_LIB_MAKEFILE_FETCH_LIB_PATTERN
from kraft.const import UNIKRAFT_LIB_MAKEFILE_URL_EXT
from kraft.const import UNIKRAFT_LIB_MAKEFILE_VERSION_EXT
from kraft.const import VSEMVER_PATTERN
from kraft.error import BumpLibraryDowngrade
from kraft.error import CannotDetermineRemoteVersion
from kraft.error import CannotReadMakefilefile
from kraft.error import NoRemoteVersionsAvailable
from kraft.error import UnknownLibraryOriginVersion
from kraft.error import UnknownLibraryProvider
from kraft.logger import logger
from kraft.template import delete_template_resources_of_disabled_features
from kraft.template import get_template_config
from kraft.template import get_templates_path
from kraft.types import ComponentType
from kraft.util import make_list_vars


def intrusively_determine_lib_origin_url(localdir=None):
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
        raise CannotReadMakefilefile(makefile_uk)

    makefile_vars = make_list_vars(makefile_uk)['makefile']

    for var in makefile_vars:
        if var.endswith(UNIKRAFT_LIB_MAKEFILE_URL_EXT):
            return makefile_vars[var]

    return None


def intrusively_determine_lib_origin_version(localdir=None):
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
        raise CannotReadMakefilefile(makefile_uk)

    makefile_vars = make_list_vars(makefile_uk)['makefile']

    for var in makefile_vars:
        if var.endswith(UNIKRAFT_LIB_MAKEFILE_VERSION_EXT):
            return makefile_vars[var]

    return None


class Library(Component):
    _type = ComponentType.LIB

    _origin_url = None

    @property
    def origin_url(self):
        """
        Returns the $(LIBNAME_VERSION) formatted string of the origin URL.
        """
        if self._origin_url is not None:
            return self._origin_url

        elif os.path.exists(self.localdir):
            self._origin_url = intrusively_determine_lib_origin_url(self._localdir)

        elif self.origin_provider is not None:
            return self.origin_provider.origin_url_with_varname(
                UK_VERSION_VARNAME % self.kname
            )

        return self._origin_url

    _origin_archive = None

    @property
    def origin_archive(self):
        """
        Returns the evaluated URL of the origin.  This is an exact location of
        the remote archive.
        """
        if self._origin_archive is not None:
            return self._origin_archive

        elif self.origin_provider is not None and self.origin_version is not None:
            origin_archive = self.origin_provider.origin_url_with_varname(
                self.origin_version
            )

        if origin_archive is not None:
            self._origin_archive = origin_archive

        elif self.origin_url is not None and self.origin_version is not None:
            self._origin_archive = self.origin_url.replace(
                UK_VERSION_VARNAME % self.kname,
                self.origin_version
            )

        return self._origin_archive

    _origin_filename = None

    @property
    def origin_filename(self):
        """
        Returns the filename of the origin from the evaluated archive URL.
        """
        if self._origin_filename is not None:
            return self._origin_filename

        elif self.origin_provider is not None:
            origin_filename = self.origin_provider.origin_filename

        if origin_filename is not None:
            self._origin_filename = origin_filename

        elif self.origin_archive is not None:
            self._origin_filename = os.path.basename(self.origin_archive)

        return self._origin_filename

    @property
    @click.pass_context
    def origin_mirrors(ctx, self):
        """
        Returns a list of evaluated origin URL mirrors.  This method uses
        information from the .kraftrc for a list of mirrors.
        """

        mirror_bases = ctx.obj.settings.fetch_mirrors
        if mirror_bases is None or len(mirror_bases) == 0:
            return []

        origin_mirrors = []

        for mirror_base in mirror_bases:
            origin_mirrors.append(os.path.join(
                mirror_base,
                "libs",
                self.name,
                self.origin_filename
            ))

        return origin_mirrors

    _origin_version = None

    @property
    def origin_version(self):
        """
        Returns the version specified in the Makefile.uk of the library, found
        from LIBNAME_VERSION.
        """
        if self._origin_version is None and os.path.exists(self.localdir):
            self._origin_version = intrusively_determine_lib_origin_version(self._localdir)

        return self._origin_version

    _origin_provider = None

    @property
    def origin_provider(self):
        """
        Heuristically determines where the origin URL is provided from.  These
        are provided as a child from the library provider class
        kraft.lib.provider.Provider.
        """
        if self._origin_provider is None and self.origin_url is not None:
            provider_cls = determine_lib_provider(self._origin_url)
            self._origin_provider = provider_cls(
                origin_url=self._origin_url,
                origin_version=self.origin_version
            )

        return self._origin_provider

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

        self._origin_url = kwargs.get("origin_url", None)
        self._origin_version = kwargs.get("origin_version", None)
        self._template_value = dict()

        self.set_template_value('year', datetime.datetime.now().year)
        self.set_template_value('project_name', self._name)
        self.set_template_value('version', self._origin_version)
        self.set_template_value('lib_name', self.libname)
        self.set_template_value('lib_kname', self.kname)
        self.set_template_value('commit', '')

    @classmethod
    @click.pass_context
    def from_workdir(ctx, cls, workdir=None):
        if workdir is None:
            workdir = ctx.obj.workdir

        return cls(
            localdir=workdir,
        )

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
        self._template_values = {
            **self._template_values,
            **dict(context['cookiecutter'])
        }

        # Set additional template values

        # Fix the starting "v" in the version string
        if context['cookiecutter']['version'].startswith('v'):
            context['cookiecutter']['version'] = context['cookiecutter']['version'][1:]
            self._origin_url = self.origin_provider.origin_url_with_varname(
                'v%s' % (UK_VERSION_VARNAME % self.kname)
            )

        context['cookiecutter']['origin_url'] = self.origin_url

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
        generate_files(
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

    @click.pass_context  # noqa: C901
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
            UnknownLibraryProvider:  Undetermined origin provider.
            KraftError:  Miscellaneous error.
        """

        if self.origin_provider is None:
            raise UnknownLibraryProvider(self.name)

        # Retrieve known versions
        versions = self.origin_provider.probe_remote_versions()

        semversions = []

        if len(versions) == 0:
            raise NoRemoteVersionsAvailable(self.origin_provider.source)

        # filter out non-semver versions
        for known_version in list(versions.keys()):
            found = SEMVER_PATTERN.search(known_version)

            if found is not None:
                semversions.append(known_version)

        current_version = self.origin_version

        if version is None:

            # Pick the highest listed verson
            if ctx.obj.assume_yes:

                # There are no semversions
                if len(semversions) == 0:
                    raise CannotDetermineRemoteVersion(self.localdir)

                current_not_semver = False

                try:
                    semver.VersionInfo.parse(current_version)
                except ValueError as e:
                    logger.warn(e)
                    current_not_semver = True

                # Remove non-semvers
                latest_version = None
                _semversions = semversions
                semversions = list()
                for checkv in _semversions:
                    try:
                        semver.VersionInfo.parse(checkv)
                        semversions.append(checkv)
                    except ValueError:
                        continue

                latest_version = sorted(semversions, reverse=True)[0]

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
                        try:
                            comparison = semver.compare(
                                semversions[i],
                                current_version
                            )
                        except ValueError as e:
                            logger.warn(e)
                            continue

                        if comparison == 0:
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
                version = read_user_choice(
                    'version',
                    sorted(list(versions.keys()), reverse=True)
                )

        if version not in versions.keys():
            if ctx.obj.assume_yes:
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

    _builddir = None

    @property
    @click.pass_context
    def builddir(ctx, self):
        if self._builddir is not None:
            return self._builddir

        if self.localdir is None:
            raise None

        if not os.path.exists(ctx.obj.workdir):
            return None

        builddir = os.path.join(ctx.obj.workdir, UNIKRAFT_BUILDDIR)
        if not os.path.exists(builddir):
            return None

        makefile_uk = os.path.join(self.localdir, MAKEFILE_UK)
        if not os.path.exists(makefile_uk):
            return None

        # Find the realy library name, at least, the name which is defined by
        # the Unikraft fetch sequence.
        s = open(makefile_uk, 'r')
        libname = UNIKRAFT_LIB_MAKEFILE_FETCH_LIB_PATTERN.findall(s.read())[0]
        s.close()

        self._builddir = os.path.join(builddir, libname)
        return self._builddir

    # TODO: Intrusively determine which additional unikraft librareis are
    # needed for this library to run.
    def determine_kconfig_dependencies(self):
        return []

    # TODO: Intrusively determine source files of the origin for the library
    def determine_source_files(self):
        return []


class LibraryManager(ComponentManager):
    def __init__(self, components=[], cls=None):
        super(LibraryManager, self).__init__(components, Library)
