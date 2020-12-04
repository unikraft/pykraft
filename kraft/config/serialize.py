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

import six
import yaml

from kraft.config import Config
from kraft.config.types import ArchitectureConfig
from kraft.config.types import LibraryConfig
from kraft.config.types import PlatformConfig
from kraft.config.types import RunnerConfig
from kraft.config.version import SpecificationVersion


def serialize_config_type(dumper, data):
    representer = dumper.represent_str if six.PY3 else dumper.represent_unicode
    return representer(data.repr())


def serialize_dict_type(dumper, data):
    return dumper.represent_dict(data.repr())


def serialize_string(dumper, data):
    """ Ensure boolean-like strings are quoted in the output """
    representer = dumper.represent_str if six.PY3 else dumper.represent_unicode

    if isinstance(data, six.binary_type):
        data = data.decode('utf-8')

    if data.lower() in ('y', 'n', 'yes', 'no', 'on', 'off', 'true', 'false'):
        # Empirically only y/n appears to be an issue, but this might change
        # depending on which PyYaml version is being used. Err on safe side.
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
    return representer(data)


def serialize_string_escape_dollar(dumper, data):
    """ Ensure boolean-like strings are quoted in the output and escape $ characters """
    data = data.replace('$', '$$')
    return serialize_string(dumper, data)


yaml.SafeDumper.add_representer(Config, serialize_dict_type)
yaml.SafeDumper.add_representer(SpecificationVersion, serialize_config_type)
yaml.SafeDumper.add_representer(ArchitectureConfig, serialize_dict_type)
yaml.SafeDumper.add_representer(PlatformConfig, serialize_dict_type)
yaml.SafeDumper.add_representer(LibraryConfig, serialize_dict_type)
yaml.SafeDumper.add_representer(RunnerConfig, serialize_dict_type)


def serialize_config(config, escape_dollar=False):
    if escape_dollar:
        yaml.SafeDumper.add_representer(str, serialize_string_escape_dollar)
        yaml.SafeDumper.add_representer(six.text_type, serialize_string_escape_dollar)
    else:
        yaml.SafeDumper.add_representer(str, serialize_string)
        yaml.SafeDumper.add_representer(six.text_type, serialize_string)
    return yaml.safe_dump(
        config,
        default_flow_style=False,
        indent=2,
        width=80,
        allow_unicode=True,
        sort_keys=False
    )
