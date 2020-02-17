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

SPECIFICATION_EXPLANATION = (
    'You might be seeing this error because you\'re using the wrong kraft file version.\n'
    'For more on the kraft file format versions, see: ttps://docs.unikraft.org/'
)

class KraftError(Exception):
    msg = None
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class KconfigFileNotFound(KraftError):
    pass

class EnvFileNotFound(KraftError):
    pass

class MisconfiguredUnikraftProject(KraftError):
    """Parameterization of the UnikraftApp was incorrect."""
    pass

class KraftFileNotFound(KraftError):
    def __init__(self, supported_filenames):
        super(KraftFileNotFound, self).__init__("""
Can't find a suitable configuration file in this directory or any
parent. Are you in the right directory?

Supported filenames: %s
""" % ", ".join(supported_filenames))


class IncompatibleKconfig(KraftError):
    def __init__(self):
        super(IncompatibleKconfig, self).__init__(
            "The provided KConfig was not compatible."
        )

class NonExistentLibrary(KraftError):
    def __init__(self):
        super(NonExistentLibrary, self).__init__("The referred library does not exist.")

class CannotReadKraftfile(KraftError):
    def __init__(self, file):
        super(CannotReadKraftfile, self).__init__("The provided file does not exist, is empty or is corrupt: %s" % file)

class InvalidInterpolation(KraftError):
    pass

class InvalidRepositoryFormat(KraftError):
    def __init__(self, repository):
        super(InvalidRepositoryFormat, self).__init__("The provided repository was not retrievable: %s" % repository)

class NoSuchReferenceInRepo(KraftError):
    def __init__(self):
        super(NoSuchReferenceInRepo, self).__init__("The provided repository does not have the specified branch.")

class NoTypeAndNameRepo(KraftError):
    def __init__(self):
        super(NoTypeAndNameRepo, self).__init__("No type and name has been provided for this repository.")

class MismatchOriginRepo(KraftError):
    def __init__(self):
        super(MismatchOriginRepo, self).__init__("A repository with a different origin has been provided")

class MismatchVersionRepo(KraftError):
    def __init__(self):
        super(MismatchVersionRepo, self).__init__("A repository with a different version has been provided")

class MismatchTargetArchitecture(KraftError):
    def __init__(self, target_arch=None, supported_archs=[]):
        if target_arch is None:
            super(MismatchTargetArchitecture, self).__init__(
                "Target architecture not set!  Supported architectures for this application include: %s" % ", ".join(supported_archs)
            )
        else:
            super(MismatchTargetArchitecture, self).__init__(
                "Target architecture (%s) set does not match the supported architectures (%s).\nPlease check your configuration." % (target_arch, ", ".join(supported_archs))
            )

class MismatchTargetPlatform(KraftError):
    def __init__(self, target_plat=None, supported_plats=[]):
        if target_plat is None:
            super(MismatchTargetPlatform, self).__init__(
                "Target platform not set!  Supported platforms for this application include: %s" % ", ".join(supported_plats)
            )
        else:
            super(MismatchTargetPlatform, self).__init__(
                "The target platform (%s) does not match the supported platforms (%s).\nPlease check your configuration." % (target_plat, ", ".join(supported_plats))
            )

class InvalidRepositorySource(KraftError):
    def __init__(self, source):
        super(InvalidRepositorySource, self).__init__("The source repository is invalid: %s" % source)

class InvalidVolumeType(KraftError):
    def __init__(self, name):
        super(InvalidVolumeType, self).__init__("The provided volume type was unknown: %s" % name)

class KraftNetworkError(KraftError):
    pass

class KraftNetworkBridgeError(KraftNetworkError):
    pass

class KraftNetworkBridgeUnsupported(KraftNetworkBridgeError):
    def __init__(self, driver):
        super(KraftNetworkBridgeUnsupported, self).__init__("bridge driver '%s' is not supported" % driver)

class InvalidBridgeName(KraftError):
    def __init__(self, name):
        super(InvalidBridgeName, self).__init__("Invalid network bridge name %s" % name)

class DNSMASQCannotStartServer(KraftError):
    def __init__(self, message):
        super(DNSMASQCannotStartServer, self).__init__("Cannot start Dnsmasq  server: %s" % message)