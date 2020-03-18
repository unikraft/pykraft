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

import logging
import os
import re

import dotenv
import six

from .errors import KraftError
from .errors import EnvFileNotFound

def split_env(env):
    if isinstance(env, six.binary_type):
        env = env.decode('utf-8', 'replace')
    key = value = None
    if '=' in env:
        key, value = env.split('=', 1)
    else:
        key = env
    if re.search(r'\s', key):
        raise KraftError(
            "environment variable name '%s' may not contain whitespace." % key
        )
    return key, value


def env_vars_from_file(filename):
    """
    Read in a line delimited file of environment variables.
    """
    if not os.path.exists(filename):
        raise EnvFileNotFound("Couldn't find env file: %s" % filename)
    elif not os.path.isfile(filename):
        raise EnvFileNotFound("%s is not a file." % filename)

    return dotenv.dotenv_values(dotenv_path=filename, encoding='utf-8-sig')


class Environment(dict):
    def __init__(self, *args, **kwargs):
        super(Environment, self).__init__(*args, **kwargs)
        self.missing_keys = []
        self.silent = False

    @classmethod
    def from_env_file(cls, base_dir, env_file=None):
        def _initialize():
            result = cls()
            if base_dir is None:
                return result
            if env_file:
                env_file_path = os.path.join(base_dir, env_file)
            else:
                env_file_path = os.path.join(base_dir, '.env')
            try:
                return cls(env_vars_from_file(env_file_path))
            except EnvFileNotFound:
                pass
            return result

        instance = _initialize()
        instance.update(os.environ)
        return instance

    @classmethod
    def from_command_line(cls, parsed_env_opts):
        result = cls()
        for k, v in parsed_env_opts.items():
            # Values from the command line take priority, unless they're unset
            # in which case they take the value from the system's environment
            if v is None and k in os.environ:
                result[k] = os.environ[k]
            else:
                result[k] = v
        return result

    def __getitem__(self, key):
        try:
            return super(Environment, self).__getitem__(key)
        except KeyError:
            if not self.silent and key not in self.missing_keys:
                logger.warning(
                    "The %s variable is not set. Defaulting to a blank string." % key
                )
                self.missing_keys.append(key)

            return ""

    def __contains__(self, key):
        result = super(Environment, self).__contains__(key)
        return result

    def get(self, key, *args, **kwargs):
        return super(Environment, self).get(key, *args, **kwargs)

    def get_boolean(self, key):
        # Convert a value to a boolean using "common sense" rules.
        # Unset, empty, "0" and "false" (i-case) yield False.
        # All other values yield True.
        value = self.get(key)
        if not value:
            return False
        if value.lower() in ['0', 'false']:
            return False
        return True
