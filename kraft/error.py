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


SPECIFICATION_EXPLANATION = ''.join([
    'You might be seeing this error because you\'re using the wrong kraft file',
    'version.\n For more on the kraft file format versions, see: ',
    'https://docs.unikraft.org/'
])


class KraftError(Exception):
    msg = None

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class KconfigFileNotFound(KraftError):
    pass


class ConfigurationError(KraftError):
    pass


class EnvFileNotFound(KraftError):
    pass


class UnsetRequiredSubstitution(KraftError):
    pass


class MisconfiguredUnikraftProject(KraftError):
    """Parameterization of the UnikraftApp was incorrect."""
    pass


class KraftFileNotFound(KraftError):
    def __init__(self, supported_filenames):
        super(KraftFileNotFound, self).__init__(
            "Can't find a suitable configuration file in this directory or any "
            + "parent. Are you in the right directory?\n\n"
            + "Supported filenames: %s" % ", ".join(supported_filenames))


class IncompatibleKconfig(KraftError):
    def __init__(self):
        super(IncompatibleKconfig, self).__init__(
            "The provided KConfig was not compatible."
        )


class NonExistentLibrary(KraftError):
    def __init__(self):
        super(NonExistentLibrary, self).__init__(
            "The referred library does not exist."
        )


class CannotReadKraftfile(KraftError):
    def __init__(self, file):
        super(CannotReadKraftfile, self).__init__(
            "The provided file does not exist, is empty or is corrupt: %s" % file
        )


class CannotReadMakefilefile(KraftError):
    def __init__(self, file):
        super(CannotReadMakefilefile, self).__init__(
            "The provided Makefile does not exist, is empty or is corrupt: %s" % file
        )


class CannotConfigureApplication(KraftError):
    def __init__(self, workdir):
        super(CannotConfigureApplication, self).__init__(
            "Cannot configure the application at %s" % workdir
        )


class InvalidInterpolation(KraftError):
    pass


class InvalidRepositoryFormat(KraftError):
    def __init__(self, repository):
        super(InvalidRepositoryFormat, self).__init__(
            "The provided repository was not retrievable: %s" % repository
        )


class NoSuchReferenceInRepo(KraftError):
    def __init__(self):
        super(NoSuchReferenceInRepo, self).__init__(
            "The provided repository does not have the specified branch."
        )


class NoTypeAndNameRepo(KraftError):
    def __init__(self):
        super(NoTypeAndNameRepo, self).__init__(
            "No type and name has been provided for this repository."
        )


class MismatchOriginRepo(KraftError):
    def __init__(self):
        super(MismatchOriginRepo, self).__init__(
            "A repository with a different origin has been provided"
        )


class MismatchVersionRepo(KraftError):
    def __init__(self):
        super(MismatchVersionRepo, self).__init__(
            "A repository with a different version has been provided"
        )


class MismatchTargetArchitecture(KraftError):
    def __init__(self, target_arch=None, supported_archs=[]):
        super(MismatchTargetArchitecture, self).__init__(
            "Supported architectures for this application include: %s"
            % ", ".join(supported_archs)
        )


class MismatchTargetPlatform(KraftError):
    def __init__(self, target_plat=None, supported_plats=[]):
        super(MismatchTargetPlatform, self).__init__(
            "Supported platforms for this application include: %s"
            % ", ".join(supported_plats)
        )


class InvalidRepositorySource(KraftError):
    def __init__(self, source):
        super(InvalidRepositorySource, self).__init__(
            "The source repository is invalid: %s" % source
        )


class InvalidVolumeDriver(KraftError):
    def __init__(self, name):
        super(InvalidVolumeDriver, self).__init__(
            "The provided volume driver was unknown: %s" % name
        )


class NetworkError(KraftError):
    pass


class NetworkDriverError(NetworkError):
    pass


class NetworkBridgeUnsupported(NetworkDriverError):
    def __init__(self, driver):
        super(NetworkBridgeUnsupported, self).__init__(
            "bridge driver '%s' is not supported" % driver
        )


class InvalidBridgeName(KraftError):
    def __init__(self, name):
        super(InvalidBridgeName, self).__init__(
            "Invalid network bridge name %s" % name
        )


class DNSMASQCannotStartServer(KraftError):
    def __init__(self, message):
        super(DNSMASQCannotStartServer, self).__init__(
            "Cannot start Dnsmasq  server: %s" % message
        )


class RunnerError(KraftError):
    pass


class UnknownLibraryProvider(KraftError):
    def __init__(self, name):
        from kraft.lib.provider.type import LibraryProviderType
        super(UnknownLibraryProvider, self).__init__(
            "The provided origin provider is not known: %s\nValid providers include: %s" % (
                name,
                ", ".join([member.name for _, member in LibraryProviderType.__members__.items()])
            )
        )


class CannotConnectURLError(KraftError):
    def __init__(self, url, msg):
        super(CannotConnectURLError, self).__init__(
            "Cannot connect to remote: %s: %s" % (url, msg)
        )


class NonCompatibleUnikraftLibrary(KraftError):
    def __init__(self, path):
        super(NonCompatibleUnikraftLibrary, self).__init__(
            "Not a Unikraft library at: %s" % path
        )


class UnknownVersionError(KraftError):
    def __init__(self, desired_version, known_versions):
        from kraft.manifest import ManifestItem

        manifest = None
        if isinstance(known_versions, ManifestItem):
            manifest = known_versions
            known_versions = list()
            for dist in manifest.dists:
                for ver in manifest.dists[dist].versions:
                    known_versions.append("%s:%s" % (dist, ver))

        if manifest is None:
            if len(known_versions) > 0:
                super(UnknownVersionError, self).__init__(
                    "Version not specified, choice of: {\n\t%s\n}" %
                    ",\n\t".join(known_versions)
                )
            else:
                super(UnknownVersionError, self).__init__(
                    "Version not specified"
                )
        else:
            if isinstance(known_versions, ManifestItem):
                if desired_version is None:
                    super(UnknownVersionError, self).__init__(
                        "No version specified for %s. Choice of: {\n\t%s\n}" % (
                            manifest.name,
                            ",\n\t".join(known_versions)
                        )
                    )
                else:
                    super(UnknownVersionError, self).__init__(
                        "Provided version '%s' for %s.  Choice of: {\n\t%s\n}" % (
                            desired_version,
                            manifest.name,
                            ",\n\t".join(known_versions)
                        )
                    )
            else:
                super(UnknownVersionError, self).__init__(
                    "No version specified for %s.  Choice of: {\n\t%s\n}" % (
                        manifest.name,
                        ",\n\t".join(known_versions)
                    )
                )


class UnknownLibraryOriginVersion(KraftError):
    def __init__(self, desired_version, known_versions):
        super(UnknownLibraryOriginVersion, self).__init__(
            "Provided version '%s' not known in: {%s}" % (desired_version, ', '.join(known_versions))
        )


class DisabledComponentError(KraftError):
    def __item__(self, name):
        super(DisabledComponentError, self).__init__(
            "Attempting to use component %s which has been disabled" % name
        )


class MissingManifest(KraftError):
    def __init__(self, name):
        super(MissingManifest, self).__init__(
            "Cannot initialize component for %s without manifest" % name
        )


class MissingComponent(KraftError):
    def __init__(self, name):
        super(MissingComponent, self).__init__(
            "Cannot initialize application without component: %s" % name
        )


class UnknownApplicationTemplateName(KraftError):
    def __init__(self, name):
        super(UnknownApplicationTemplateName, self).__init__(
            "Unknown application name: %s" % name
        )


class UnknownVersionFormatError(KraftError):
    def __init__(self, name):
        super(UnknownVersionFormatError, self).__init__(
            "String does not contain equality: %s"
            % (name)
        )


class BumpLibraryDowngrade(KraftError):
    def __init__(self, current_version, desired_version):
        super(BumpLibraryDowngrade, self).__init__(
            "Attempting to downgrade library from %s to %s!  Use -f to override."
            % (current_version, desired_version)
        )


class NoRemoteVersionsAvailable(KraftError):
    def __init__(self, origin):
        super(NoRemoteVersionsAvailable, self).__init__(
            "Unable to retrieve remote versions for: %s" % origin
        )


class CannotDetermineRemoteVersion(KraftError):
    def __init__(self, origin):
        super(NoRemoteVersionsAvailable, self).__init__(
            "Unable to determine latest version: %s" % origin
        )
