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

import re
from string import Template

import six

from kraft.error import ConfigurationError
from kraft.error import InvalidInterpolation
from kraft.error import UnsetRequiredSubstitution


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


def recursive_interpolate(obj, interpolator, config_path):
    def append(config_path, key):
        return '{}/{}'.format(config_path, key)

    if isinstance(obj, six.string_types):
        return converter.convert(config_path, interpolator.interpolate(obj))

    if isinstance(obj, dict):
        return dict(
            (key, recursive_interpolate(val, interpolator, append(config_path, key)))
            for (key, val) in obj.items()
        )

    if isinstance(obj, list):
        return [recursive_interpolate(val, interpolator, config_path) for val in obj]

    return converter.convert(config_path, obj)


def get_config_path(config_key, section, name):
    return '{}/{}/{}'.format(section, name, config_key)


def interpolate_value(name, config_key, value, section, interpolator):
    try:
        return recursive_interpolate(value, interpolator, get_config_path(config_key, section, name))

    except InvalidInterpolation as e:
        raise ConfigurationError(
            'Invalid interpolation format for "{config_key}" option '
            'in {section} "{name}": "{string}"'.format(
                config_key=config_key,
                name=name,
                section=section,
                string=e.string))

    except UnsetRequiredSubstitution as e:
        raise ConfigurationError(
            'Missing mandatory value for "{config_key}" option interpolating {value} '
            'in {section} "{name}": {err}'.format(config_key=config_key,
                                                  value=value,
                                                  name=name,
                                                  section=section,
                                                  err=e.err)
        )


def interpolate_environment_variables(version, config, section, environment):
    interpolator = Interpolator(TemplateWithDefaults, environment)

    def process_item(name, config_dict):
        if isinstance(config_dict, six.string_types):
            return interpolator.interpolate(config_dict)

        elif isinstance(config_dict, list):
            return list(
                interpolator.interpolate(val)
                for val in config_dict
            )

        elif isinstance(config_dict, dict):
            return dict(
                (key, interpolate_value(name, key, val, section, interpolator))
                for key, val in (config_dict or {}).items()
            )

        return config_dict

    if isinstance(config, six.string_types):
        return interpolator.interpolate(config)

    elif isinstance(config, list):
        return list(
            process_item(None, config_dict or {})
            for config_dict in config
        )

    elif isinstance(config, dict):
        return dict(
            (name, process_item(name, config_dict or {}))
            for name, config_dict in config.items()
        )

    return config


class ConversionMap(object):
    map = {}

    def convert(self, path, value):
        for rexp in self.map.keys():
            if rexp.match(path):
                try:
                    return self.map[rexp](value)
                except ValueError as e:
                    raise ConfigurationError(
                        'Error while attempting to convert {} to appropriate type: {}'.format(
                            path.replace('/', '.'), e
                        )
                    )
        return value


converter = ConversionMap()
