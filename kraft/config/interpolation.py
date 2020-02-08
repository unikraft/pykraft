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

import re
from string import Template

from kraft.constants import UNIKRAFT_ORG
from kraft.constants import UNIKRAFT_CORE
from kraft.constants import GITHUB_ORIGIN
from kraft.constants import ORG_DELIMETERE
from kraft.constants import REPO_VERSION_DELIMETERE
from kraft.constants import REPO_VALID_URL_PREFIXES

from kraft.component import Component
from kraft.errors import InvalidInterpolation
from kraft.errors import InvalidRepositorySource

class Interpolator(object):

    def __init__(self, templater, mapping):
        self.templater = templater
        self.mapping = mapping

    def interpolate(self, string):
        try:
            return self.templater(string).substitute(self.mapping)
        except ValueError:
            raise InvalidInterpolation(string)

class TemplateWithDefaults(Template):
    pattern = r"""
        %(delim)s(?:
            (?P<escaped>%(delim)s) |
            (?P<named>%(id)s)      |
            {(?P<braced>%(bid)s)}  |
            (?P<invalid>)
        )
        """ % {
        'delim': re.escape('$'),
        'id': r'[_a-z][_a-z0-9]*',
        'bid': r'[_a-z][_a-z0-9]*(?:(?P<sep>:?[-?])[^}]*)?',
    }

    @staticmethod
    def process_braced_group(braced, sep, mapping):
        if ':-' == sep:
            var, _, default = braced.partition(':-')
            return mapping.get(var) or default
        elif '-' == sep:
            var, _, default = braced.partition('-')
            return mapping.get(var, default)

        elif ':?' == sep:
            var, _, err = braced.partition(':?')
            result = mapping.get(var)
            if not result:
                raise UnsetRequiredSubstitution(err)
            return result
        elif '?' == sep:
            var, _, err = braced.partition('?')
            if var in mapping:
                return mapping.get(var)
            raise UnsetRequiredSubstitution(err)

    # Modified from python2.7/string.py
    def substitute(self, mapping):
        # Helper function for .sub()

        def convert(mo):
            named = mo.group('named') or mo.group('braced')
            braced = mo.group('braced')
            if braced is not None:
                sep = mo.group('sep')
                if sep:
                    return self.process_braced_group(braced, sep, mapping)

            if named is not None:
                val = mapping[named]
                if isinstance(val, six.binary_type):
                    val = val.decode('utf-8')
                return '%s' % (val,)
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                self._invalid(mo)
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)

def interpolate_environment_variables(version, config, section, environment):
    
    interpolator = Interpolator(TemplateWithDefaults, environment)

    def process_item(name, config_dict):
        return dict(
            (key, interpolate_value(name, key, val, section, interpolator))
            for key, val in (config_dict or {}).items()
        )
    
    if isinstance(config, dict):
        return config
    else:
        return dict(
            (name, process_item(name, config_dict or {}))
            for name, config_dict in config.items()
        )

def interpolate_source_version(name=None, source=None, version=None, component_type=None):
    """Parse a well-known repository naming format such that a Repository
    object is realized.

    The general semantics for a source string are:
    
        <ORIGIN>@<BRANCH, TAG or COMMIT HASH>.

    This allows for a fully qualified source origin, for example:
    
        git://git@github.com/unikraft/unikraft.git@v0.4.0
        https://github.com/unikraft/unikraft.git@v0.4.0
        file:///root/unikraft/libs/my-lib@staging

    Additionally, an abbreviated source can also be provided such that its
    origin is inferred from Unikraft's Github organization.  This means
    providing the following will qualify as valid and inferred,
    respectively, sources:

        - v0.4.0 -> https://github.com.unikraft/unikraft.git@v0.4.0
        - lib-lwip -> https://github.com.unikraft/lib-lwip.git@master
        - lib-lwip@v0.4.0 -> https://github.com.unikraft/lib-lwip.git@v0.4.0
        - unikraft/lib-lwip -> https://github.com.unikraft/lib-lwip.git@master
        - unikraft/lib-lwip@staging -> https://github.com/unikraft/lib-lwip.git@staging
    """

    if source is None:
        if version is None:
            raise InvalidRepositorySource(source)
        else:
            source = version
            version = None

    # First determine if the provided string has a version
    if REPO_VERSION_DELIMETERE in source:
        source, version = source.split(REPO_VERSION_DELIMETERE, 1)

        # The source could be accessible via ssh (user@host), remedy this:
        if REPO_VERSION_DELIMETERE in version:
            x, version = version.split(REPO_VERSION_DELIMETERE, 1)
            source = source + REPO_VERSION_DELIMETERE + x

    # If it's not a valid URL source, we must begin to make assumptions
    if not source.startswith(REPO_VALID_URL_PREFIXES):

        # Check if a reference to a Github org/repo:
        if ORG_DELIMETERE in source:
            source = "%s/%s" % (GITHUB_ORIGIN, source)
        
        # Does the repository start with lib-, plat-, etc.?
        elif source.startswith(tuple(y.shortname + '-' for x, y in Component.__members__.items())):
            source = "%s/%s/%s" % (GITHUB_ORIGIN, UNIKRAFT_ORG, source)

        # Can we inference anything from its name (which will have been
        # retrieved from the configuration prefix, e.g. my-lib: version)
        elif name is not None and component_type is Component.LIB:
            version = source
            source = "%s/%s/lib-%s" % (GITHUB_ORIGIN, UNIKRAFT_ORG, name)

        # Assuming it's a version tag for the main unikraft repo:
        elif version is None:
            version = source
            source = UNIKRAFT_CORE
        
        # Of the format "unikraft@version"
        elif source == UNIKRAFT_ORG:
            source = UNIKRAFT_CORE

        else:
            raise InvalidRepositorySource(source)

    # Still no version?  Try master
    if version is None:
        version = BRANCH_MASTER
    
    return source, version
