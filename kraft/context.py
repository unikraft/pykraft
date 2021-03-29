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

import logging
import os
import pkgutil
from pathlib import Path

from kraft.cache import Cache
from kraft.config.environment import Environment
from kraft.const import KRAFTRC
from kraft.const import UNIKRAFT_APPSDIR
from kraft.const import UNIKRAFT_ARCHSDIR
from kraft.const import UNIKRAFT_BUILDDIR
from kraft.const import UNIKRAFT_CACHEDIR
from kraft.const import UNIKRAFT_COREDIR
from kraft.const import UNIKRAFT_LIBSDIR
from kraft.const import UNIKRAFT_PLATSDIR
from kraft.const import UNIKRAFT_WORKDIR
from kraft.logger import logger
from kraft.settings import Settings


class KraftContext:
    """
    Context manager acts as a decorator and helps initialize and persist and
    current state of affairs for the kraft utility.
    """

    _verbose = False
    _timestamps = True
    _assume_yes = False
    _dont_checkout = False
    _ignore_checkout_errors = False

    def __init__(self, verbose=False, dont_checkout=False,
                 ignore_checkout_errors=False, assume_yes=False):
        self.verbose = verbose
        self._dont_checkout = dont_checkout
        self._ignore_checkout_errors = ignore_checkout_errors
        self._assume_yes = assume_yes
        self._workdir = os.getcwd()
        self._depth = 0
        self._close_callbacks = []
        self._timestamps = True
        self.obj = self
        self.init_env()

    def init_env(self):  # noqa: C901
        """
        Determines whether the integrity of the kraft application, namely
        determining whether the kraft application can run under the given
        runtime environment.
        """

        if 'UK_CACHEDIR' not in os.environ:
            os.environ['UK_CACHEDIR'] = os.path.join(os.environ['HOME'], UNIKRAFT_CACHEDIR)
        if 'UK_WORKDIR' not in os.environ:
            os.environ['UK_WORKDIR'] = os.path.join(os.environ['HOME'], UNIKRAFT_WORKDIR)
        if os.path.isdir(os.environ['UK_WORKDIR']) is False:
            os.mkdir(os.environ['UK_WORKDIR'])
        if 'UK_ROOT' not in os.environ:
            os.environ['UK_ROOT'] = os.path.join(os.environ['UK_WORKDIR'], UNIKRAFT_COREDIR)
        if os.path.isdir(os.environ['UK_ROOT']) is False:
            os.mkdir(os.environ['UK_ROOT'])
        if 'UK_ARCHS' not in os.environ:
            os.environ['UK_ARCHS'] = os.path.join(os.environ['UK_WORKDIR'], UNIKRAFT_ARCHSDIR)
        if os.path.isdir(os.environ['UK_ARCHS']) is False:
            os.mkdir(os.environ['UK_ARCHS'])
        if 'UK_PLATS' not in os.environ:
            os.environ['UK_PLATS'] = os.path.join(os.environ['UK_WORKDIR'], UNIKRAFT_PLATSDIR)
        if os.path.isdir(os.environ['UK_PLATS']) is False:
            os.mkdir(os.environ['UK_PLATS'])
        if 'UK_LIBS' not in os.environ:
            os.environ['UK_LIBS'] = os.path.join(os.environ['UK_WORKDIR'], UNIKRAFT_LIBSDIR)
        if os.path.isdir(os.environ['UK_LIBS']) is False:
            os.mkdir(os.environ['UK_LIBS'])
        if 'UK_APPS' not in os.environ:
            os.environ['UK_APPS'] = os.path.join(os.environ['UK_WORKDIR'], UNIKRAFT_APPSDIR)
        if os.path.isdir(os.environ['UK_APPS']) is False:
            os.mkdir(os.environ['UK_APPS'])

        # Check if we have a build-time engine set
        if 'UK_BUILD_ENGINE' not in os.environ:
            os.environ['UK_BUILD_ENGINE'] = 'gcc'

        if 'KRAFTRC' not in os.environ:
            os.environ['KRAFTRC'] = os.path.join(os.environ['HOME'], KRAFTRC)
        if os.path.exists(os.environ['KRAFTRC']) is False:
            default_kraftrc = pkgutil.get_data(__name__, KRAFTRC)
            logger.debug("Creating %s..." % os.environ['KRAFTRC'])
            if not default_kraftrc:
                Path(os.environ['KRAFTRC']).touch()
            else:
                kraftrc = open(os.environ['KRAFTRC'], "wb")
                kraftrc.write(default_kraftrc)
                kraftrc.close()

        self._env = Environment.from_env_file(self._workdir, None)
        self._cache = Cache(self.env)
        self._settings = Settings(os.environ['KRAFTRC'])

    @property
    def cache(self):
        return self._cache

    @property
    def verbose(self):
        return self._verbose

    @property
    def dont_checkout(self):
        return self._dont_checkout

    @dont_checkout.setter
    def dont_checkout(self, dont_checkout):
        self._dont_checkout = dont_checkout

    @property
    def ignore_checkout_errors(self):
        return self._ignore_checkout_errors

    @ignore_checkout_errors.setter
    def ignore_checkout_errors(self, ignore_checkout_errors):
        self._ignore_checkout_errors = ignore_checkout_errors

    @verbose.setter
    def verbose(self, verbose):
        self._verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

    @property
    def workdir(self):
        return self._workdir

    @property
    def builddir(self):
        if self.workdir is not None and os.path.exists(self.workdir):
            return os.path.join(self.workdir, UNIKRAFT_BUILDDIR)

        return None

    @workdir.setter
    def workdir(self, workdir):
        # Re-initialize an environment from a new given workding directory
        self._env = Environment.from_env_file(workdir, None)
        self._workdir = workdir

    @property
    def assume_yes(self):
        return self._assume_yes

    @assume_yes.setter
    def assume_yes(self, assume_yes=False):
        self._assume_yes = assume_yes

    @property
    def env(self):
        return self._env

    @property
    def settings(self):
        return self._settings
