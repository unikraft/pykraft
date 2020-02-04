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
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class KconfigFileNotFound(KraftError):
    pass

class EnvFileNotFound(KraftError):
    pass

class MisconfiguredUnikraftApp(KraftError):
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
    """The provided KConfiguration was not compatible."""
    pass

class NonExistentLibrary(KraftError):
    """The referred library does not exist."""
    pass

class CannotReadDepsJson(KraftError):
    """The provided file does not exist or is corrupt."""
    pass

class InvalidInterpolation(KraftError):
    pass
