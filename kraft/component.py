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
#
# THIS HEADER MAY NOT BE EXTRACTED OR MODIFIED IN ANY WAY.

import re
from enum import Enum
from kraft.logger import logger

UK_GITHUB_NAMING_FORMAT=r'(%s)-([^.]+)'
UK_GITHUB_CORE_FORMAT=re.compile(r'(unikraft)/(unikraft)')

class KraftComponent(Enum):
    CORE = ( "core" , "core"         , "core"          )
    ARCH = ( "arch" , "architecture" , "architectures" )
    PLAT = ( "plat" , "platform"     , "platforms"     )
    LIB  = ( "lib"  , "library"      , "libraries"     )
    APP  = ( "app"  , "application"  , "applications"  )

    @property
    def format(self):
        if self.shortname == "core":
            return re.compile(UK_GITHUB_CORE_FORMAT)
        else:
            return re.compile(UK_GITHUB_NAMING_FORMAT % self.shortname)

    @property
    def shortname(self):
        return self.value[0]

    @property
    def name(self):
        return self.value[1]

    @property
    def plural(self):
        return self.value[2]

    def search(self, name):
        """Search determines whether the provided input `name` is of the
        repository naming format.  The method returns the usable name for the
        repository and thus the component."""
        return self.format.search(name)

    def valid_dir(self, dir):
        """Make a reasonable attempt to determine whether the provided directory
        is valid for this component.  This is a heuristic which checks a number
        of required files depending on the component type.  Unikraft itself
        requires the files checked and the syntax of these files to be correct
        before it can use the component.  By checking the validity of the
        directory for the component we are to preemptively warn a developer of
        of any problems that may arise before the unikraft build system throws
        its own errors."""

        if self.shortname == "core":
            logger.warn("Testing the validity of unikraft core is not yet implemented!")
            return True

        elif self.shortname == "arch":
            logger.warn("Testing the validity of unikraft architecture is not yet implemented!")
            return True

        elif self.shortname == "plat":
            logger.warn("Testing the validity of unikraft platform is not yet implemented!")
            return True

        elif self.shortname == "lib":
            logger.warn("Testing the validity of unikraft library is not yet implemented!")
            return True

        elif self.shortname == "app":
            logger.warn("Testing the validity of unikraft application is not yet implemented!")
            return True

