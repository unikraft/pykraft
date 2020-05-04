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

import logging
import os
from pathlib import Path

import click

from kraft.cache import Cache
from kraft.constants import KRAFTCONF
from kraft.constants import UNIKRAFT_APPSDIR
from kraft.constants import UNIKRAFT_COREDIR
from kraft.constants import UNIKRAFT_LIBSDIR
from kraft.constants import UNIKRAFT_WORKDIR
from kraft.environment import Environment
from kraft.logger import logger
from kraft.settings import Settings


class Context(click.Context):
    _verbose = False
    _dont_checkout = False
    _timestamps = True
    ignore_checkout_errors = False

    """Context manager acts as a decorator and helps initialize and persist and
    current state of affairs for the kraft utility."""
    def __init__(self):
        self._verbose = False
        self._workdir = os.getcwd()
        self.init_env()
        self._depth = 0
        self._close_callbacks = []
        self.obj = self
        self._cache = Cache(self.env)
        self._settings = Settings(os.environ['KRAFTCONF'])
        self._timestamps = True

    def init_env(self):  # noqa: C901
        """Determines whether the integrity of the kraft application, namely
        determining whether the kraft application can run under the given
        runtime environment."""

        if 'UK_WORKDIR' not in os.environ:
            os.environ['UK_WORKDIR'] = os.path.join(os.environ['HOME'], UNIKRAFT_WORKDIR)
        if os.path.isdir(os.environ['UK_WORKDIR']) is False:
            os.mkdir(os.environ['UK_WORKDIR'])
        if 'UK_ROOT' not in os.environ:
            os.environ['UK_ROOT'] = os.path.join(os.environ['UK_WORKDIR'], UNIKRAFT_COREDIR)
        if os.path.isdir(os.environ['UK_ROOT']) is False:
            os.mkdir(os.environ['UK_ROOT'])
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

        if 'KRAFTCONF' not in os.environ:
            os.environ['KRAFTCONF'] = os.path.join(os.environ['HOME'], KRAFTCONF)
        if os.path.exists(os.environ['UK_APPS']) is False:
            Path(os.environ['UK_APPS']).touch()

        self._env = Environment.from_env_file(self._workdir, None)

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

    @workdir.setter
    def workdir(self, workdir):
        # Re-initialize an environment from a new given workding directory
        self._env = Environment.from_env_file(workdir, None)
        self._workdir = workdir

    @property
    def env(self):
        return self._env

    @property
    def settings(self):
        return self._settings


kraft_context = click.make_pass_decorator(Context, ensure=True)
