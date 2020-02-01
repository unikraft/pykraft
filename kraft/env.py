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

import os
import click
from .cache import Cache
from .logger import logger

class Environment(object):
    def __init__(self):
        self.sanity_check()
        self.verbose = False
        self.workdir = os.getcwd()
        self.init_caching()

    def sanity_check(self):
        """Determines whether the integrity of the kraft application, namely
        determining whether the kraft application can run under the given
        runtime environment."""

        if 'UK_WORKDIR' not in os.environ:
            os.environ['UK_WORKDIR'] = os.environ['HOME'] + '/.unikraft'
        if os.path.isdir(os.environ['UK_WORKDIR']) is False:
            os.mkdir(os.environ['UK_WORKDIR'])
        if 'UK_ROOT' not in os.environ:
            os.environ['UK_ROOT'] = os.environ['UK_WORKDIR'] + '/unikraft'
        if os.path.isdir(os.environ['UK_ROOT']) is False:
            os.mkdir(os.environ['UK_ROOT'])
        if 'UK_LIBS' not in os.environ:
            os.environ['UK_LIBS'] = os.environ['UK_WORKDIR'] + '/libs'
        if os.path.isdir(os.environ['UK_LIBS']) is False:
            os.mkdir(os.environ['UK_LIBS'])
        if 'UK_APPS' not in os.environ:
            os.environ['UK_APPS'] = os.environ['UK_WORKDIR'] + '/apps'
        if os.path.isdir(os.environ['UK_APPS']) is False:
            os.mkdir(os.environ['UK_APPS'])

        # Check if we have a build-time engine set
        if 'UK_BUILD_ENGINE' not in os.environ:
            os.environ['UK_BUILD_ENGINE'] = 'gcc'


    def init_caching(self):
        """Initializes the cache so that kraft does not have to constantly
        retrieve informational lists about unikraft, its available architectures,
        platforms, libraries and supported applications.

        The 'c' means that the object will open a cache if it exists, but will
        create a new one if no cache is found. The 's' means that the cache is
        opened in sync mode. All changes are immediately written to disk."""
        self.cache = Cache()

pass_environment = click.make_pass_decorator(Environment, ensure=True)
