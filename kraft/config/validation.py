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

        if not isinstance(value, (dict, type(None))):
            raise KraftError(
                "In file '{filename}', {section} '{name}' must be a mapping not "
                "{type}.".format(
                    filename=filename,
                    section=section,
                    name=key,
                    type=anglicize_json_type(python_type_to_yaml_type(value))))

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