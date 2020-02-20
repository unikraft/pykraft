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

import os
import six
import json

from jsonschema import Draft4Validator
from jsonschema import RefResolver

from kraft.errors import KraftError
from kraft.errors import SPECIFICATION_EXPLANATION

def python_type_to_yaml_type(type_):
    type_name = type(type_).__name__
    return {
        'dict': 'mapping',
        'list': 'array',
        'int': 'number',
        'float': 'number',
        'bool': 'boolean',
        'unicode': 'string',
        'str': 'string',
        'bytes': 'string',
    }.get(type_name, type_name)

def anglicize_json_type(json_type):
    if json_type.startswith(('a', 'e', 'i', 'o', 'u')):
        return 'an ' + json_type
    return 'a ' + json_type

def validate_top_level_string(filename, config, section):
    if not isinstance(config, six.string_types):
        raise KraftError(
            "Top level object in '{}' needs to be a string not '{}'.".format(
                config_file.filename,
                type(config)))

def validate_unikraft_section(config_file, config):
    if not isinstance(config, (six.string_types, dict)):
        raise KraftError(
            "Top level object in '{}' needs to be an object not '{}'.".format(
                config_file.filename,
                type(config)))

def validate_libraries_section(config_file, config):
    # if not isinstance(value, (dict, six.string_types, type(None))):
    if not isinstance(config, (six.string_types, dict)):
        raise KraftError(
            "Top level object in '{}' needs to be an object not '{}'.".format(
                config_file.filename,
                type(config)))

def validate_config_section(filename, config, section):
    """Validate the structure of a configuration section. This must be done
    before interpolation so it's separate from schema validation.
    """
    if not isinstance(config, dict):
        raise KraftError(
            "In file '{filename}', {section} must be a mapping, not "
            "{type}.".format(
                filename=filename,
                section=section,
                type=anglicize_json_type(python_type_to_yaml_type(config))))

    for key, value in config.items():
        if not isinstance(key, six.string_types):
            raise KraftError(
                "In file '{filename}', the {section} name {name} must be a "
                "quoted string, i.e. '{name}'.".format(
                    filename=filename,
                    section=section,
                    name=key))

        if not isinstance(value, (dict, bool)):
            raise KraftError(
                "In file '{filename}', {section} '{name}' must be a mapping not "
                "{type}.".format(
                    filename=filename,
                    section=section,
                    name=key,
                    type=anglicize_json_type(python_type_to_yaml_type(value))))

def validate_executor_section(config_file, config):
    if not isinstance(config, dict):
        raise KraftError(
            "Top level object in '{}' needs to be an object not '{}'.".format(
                config_file.filename,
                type(config)))

def get_schema_path():
    return os.path.dirname(os.path.abspath(__file__))

def load_jsonschema(config_file):
    filename = os.path.join(
        get_schema_path(),
        "specification_v{0}.json".format(config_file.version)
    )

    if not os.path.exists(filename):
        raise KraftError(
            'Specification in "{}" is unsupported. {}'
            .format(config_file.filename, SPECIFICATION_EXPLANATION))

    with open(filename, "r") as fh:
        return json.load(fh)

def get_resolver_path():
    return "file://%s/" % get_schema_path()

def parse_key_from_error_msg(error):
    try:
        return error.message.split("'")[1]
    except IndexError:
        return error.message.split('(')[1].split(' ')[0].strip("'")

def handle_error_for_schema_with_id(error, path):
    schema_id = error.schema['id']
    
    if error.validator == 'additionalProperties':
        if schema_id.startswith('specification_v'):
            invalid_config_key = parse_key_from_error_msg(error)
            return ('Invalid top-level property "{key}". Valid top-level '
                    'sections for this Kraft file are: {properties}.\n\n{explanation}').format(
                key=invalid_config_key,
                properties=', '.join(error.schema['properties'].keys()),
                explanation=SPECIFICATION_EXPLANATION
            )

        if not error.path:
            return '{}\n\n{}'.format(error.message, SPECIFICATION_EXPLANATION)


def path_string(path):
    return ".".join(c for c in path if isinstance(c, six.string_types))


def _parse_valid_types_from_validator(validator):
    """A validator value can be either an array of valid types or a string of
    a valid type. Parse the valid types and prefix with the correct article.
    """
    if not isinstance(validator, list):
        return anglicize_json_type(validator)

    if len(validator) == 1:
        return anglicize_json_type(validator[0])

    return "{}, or {}".format(
        ", ".join([anglicize_json_type(validator[0])] + validator[1:-1]),
        anglicize_json_type(validator[-1]))

def _parse_oneof_validator(error):
    """oneOf has multiple schemas, so we need to reason about which schema, sub
    schema or constraint the validation is failing on.
    Inspecting the context value of a ValidationError gives us information about
    which sub schema failed and which kind of error it is.
    """
    types = []
    for context in error.context:
        if context.validator == 'oneOf':
            _, error_msg = _parse_oneof_validator(context)
            return path_string(context.path), error_msg

        if context.validator == 'required':
            return (None, context.message)

        if context.validator == 'additionalProperties':
            invalid_config_key = parse_key_from_error_msg(context)
            return (None, "contains unsupported option: '{}'".format(invalid_config_key))

        if context.validator == 'uniqueItems':
            return (
                path_string(context.path) if context.path else None,
                "contains non-unique items, please remove duplicates from {}".format(
                    context.instance),
            )

        if context.path:
            return (
                path_string(context.path),
                "contains {}, which is an invalid type, it should be {}".format(
                    json.dumps(context.instance),
                    _parse_valid_types_from_validator(context.validator_value)),
            )

        if context.validator == 'type':
            types.append(context.validator_value)

    valid_types = _parse_valid_types_from_validator(types)
    return (None, "contains an invalid type, it should be {}".format(valid_types))

def handle_generic_error(error, path):
    msg_format = None
    error_msg = error.message

    if error.validator == 'oneOf':
        msg_format = "{path} {msg}"
        config_key, error_msg = _parse_oneof_validator(error)
        if config_key:
            path.append(config_key)

    elif error.validator == 'type':
        msg_format = "{path} contains an invalid type, it should be {msg}"
        error_msg = _parse_valid_types_from_validator(error.validator_value)

    elif error.validator == 'required':
        error_msg = ", ".join(error.validator_value)
        msg_format = "{path} is invalid, {msg} is required."

    elif error.validator == 'dependencies':
        config_key = list(error.validator_value.keys())[0]
        required_keys = ",".join(error.validator_value[config_key])

        msg_format = "{path} is invalid: {msg}"
        path.append(config_key)
        error_msg = "when defining '{}' you must set '{}' as well".format(
            config_key,
            required_keys)

    elif error.cause:
        error_msg = six.text_type(error.cause)
        msg_format = "{path} is invalid: {msg}"

    elif error.path:
        msg_format = "{path} value {msg}"

    if msg_format:
        return msg_format.format(path=path_string(path), msg=error_msg)

    return error.message

def process_config_schema_errors(error):
    path = list(error.path)

    if 'id' in error.schema:
        error_msg = handle_error_for_schema_with_id(error, path)
        if error_msg:
            return error_msg

    return handle_generic_error(error, path)

def handle_errors(errors, format_error_func, filename):
    """jsonschema returns an error tree full of information to explain what has
    gone wrong. Process each error and pull out relevant information and re-write
    helpful error messages that are relevant.
    """
    errors = list(sorted(errors, key=str))
    if not errors:
        return

    error_msg = '\n'.join(format_error_func(error) for error in errors)
    raise KraftError(
        "The Kraft file{file_msg} is invalid because:\n{error_msg}".format(
            file_msg=" '{}'".format(filename) if filename else "",
            error_msg=error_msg))

def validate_against_config_schema(config_file):
    schema = load_jsonschema(config_file)
    # format_checker = FormatChecker(["..."])
    validator = Draft4Validator(
        schema,
        resolver=RefResolver(get_resolver_path(), schema),
        # format_checker=format_checker
    )
    handle_errors(
        validator.iter_errors(config_file.config),
        process_config_schema_errors,
        config_file.filename)