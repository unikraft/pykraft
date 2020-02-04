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

import os
import io
import re
import yaml

from collections import namedtuple
from cached_property import cached_property

from .version import SpecificationVersion
from .validation import validate_config_section
from .interpolation import interpolate_environment_variables
from .validation import validate_against_config_schema

from kraft.errors import KraftError
from kraft.errors import KraftFileNotFound
from kraft.logger import logger

SUPPORTED_FILENAMES = [
    'kraft.yml',
    'kraft.yaml',
]

SOURCE_VALID_URL_PREFIXES = (
    'http://',
    'https://',
    'git://',
    'github.com/',
    'git@',
)

class ConfigDetails(namedtuple('_ConfigDetails', 'working_dir config_files environment')):
    """
    :param working_dir: the directory to use for relative paths in the config
    :type  working_dir: string
    :param config_files: list of configuration files to load
    :type  config_files: list of :class:`ConfigFile`
     """
    def __new__(cls, working_dir, config_files, environment=None):
        if environment is None:
            environment = Environment.from_env_file(working_dir)
        return super(ConfigDetails, cls).__new__(
            cls, working_dir, config_files, environment
        )

class ConfigFile(namedtuple('_ConfigFile', 'filename config')):
    """
    :param filename: filename of the config file
    :type  filename: string
    :param config: contents of the config file
    :type  config: :class:`dict`
    """

    @classmethod
    def from_filename(cls, filename):
        return cls(filename, load_yaml(filename))

    @cached_property
    def version(self):
        if 'specification' not in self.config:
            return V1

        version = self.config['specification']

        version_pattern = re.compile(r"^[1-9]+(\.\d+)?$")
        if not version_pattern.match(version):
            raise KraftError(
                'Specification "{}" in "{}" is invalid.'
                .format(version, self.filename))

        return SpecificationVersion(version)

    def get_unikraft(self):
        return self.config.get('unikraft', {})

    def get_architecture(self, name):
        return self.get_architectures()[name]

    def get_architectures(self):
        return self.config.get('architectures', {})

    def get_platform(self, name):
        return self.get_platforms()[name]

    def get_platforms(self):
        return self.config.get('platforms', {})

    def get_library(self, name):
        return self.get_libraries()[name]

    def get_libraries(self):
        return self.config.get('libraries', {})

    def get_volumes(self):
        return self.config.get('volumes', {})

    def get_networks(self):
        return self.config.get('networks', {})

class Config(namedtuple('_Config', 'specification unikraft architectures platforms libraries volumes')):
    """
    :param specification: configuration version
    :type  specification: int

    :param unikraft: Unikraft's core configuration
    :type  unikraft: :class:`dict`

    :param architectures: Dictionary mapping architecture names to description dictionaries
    :type  architectures: :class:`dict`

    :param platforms: Dictionary mapping platform names to description dictionaries
    :type  platforms: :class:`dict`

    :param libraries: Dictionary mapping library names to description dictionaries
    :type  libraries: :class:`dict`

    :param volumes: Dictionary mapping file system names to description dictionaries
    :type  volumes: :class:`dict`
    """



def process_config_section(config_file, config, section, environment, interpolate):
    validate_config_section(config_file.filename, config, section)
    if interpolate:
        return interpolate_environment_variables(
            config_file.version,
            config,
            section,
            environment
            )
    else:
        return config

def process_config_file(config_file, environment, service_name=None, interpolate=True):

    processed_config = dict(config_file.config)

    processed_config['unikraft'] = process_config_section(
        config_file,
        config_file.get_unikraft(),
        'unikraft',
        environment,
        interpolate,
    )
    processed_config['architectures'] = process_config_section(
        config_file,
        config_file.get_architectures(),
        'architectures',
        environment,
        interpolate,
    )
    processed_config['platforms'] = process_config_section(
        config_file,
        config_file.get_platforms(),
        'platforms',
        environment,
        interpolate,
    )
    processed_config['libraries'] = process_config_section(
        config_file,
        config_file.get_libraries(),
        'libraries',
        environment,
        interpolate,
    )
    processed_config['volumes'] = process_config_section(
        config_file,
        config_file.get_volumes(),
        'volumes',
        environment,
        interpolate,
    )

    config_file = config_file._replace(config=processed_config)
    validate_against_config_schema(config_file)

    return config_file


def find_candidates_in_parent_dirs(filenames, path):
    """
    Given a directory path to start, looks for filenames in the
    directory, and then each parent directory successively,
    until found.

    Returns tuple (candidates, path).
    """
    candidates = [filename for filename in filenames
                  if os.path.exists(os.path.join(path, filename))]

    if not candidates:
        parent_dir = os.path.join(path, '..')
        if os.path.abspath(parent_dir) != os.path.abspath(path):
            return find_candidates_in_parent_dirs(filenames, parent_dir)

    return (candidates, path)

def get_default_config_files(base_dir):
    (candidates, path) = find_candidates_in_parent_dirs(SUPPORTED_FILENAMES, base_dir)

    if not candidates:
        raise KraftFileNotFound(SUPPORTED_FILENAMES)

    winner = candidates[0]

    if len(candidates) > 1:
        log.warning("Found multiple config files with supported names: %s", ", ".join(candidates))
        log.warning("Using %s\n", winner)

    return [os.path.join(path, winner)]

def find(base_dir, filenames, environment, override_dir=None):
    if filenames == ['-']:
        return ConfigDetails(
            os.path.abspath(override_dir) if override_dir else os.getcwd(),
            [ConfigFile(None, yaml.safe_load(sys.stdin))],
            environment
        )

    if filenames:
        filenames = [os.path.join(base_dir, f) for f in filenames]
    else:
        filenames = get_default_config_files(base_dir)

    logger.debug("Using configuration files: %s" % (",".join(filenames)))
    return ConfigDetails(
        override_dir if override_dir else os.path.dirname(filenames[0]),
        [ConfigFile.from_filename(f) for f in filenames],
        environment
    )


def load_mapping(config_files, get_func, entity_type, working_dir=None):
    mapping = {}

    for config_file in config_files:
        for name, config in getattr(config_file, get_func)().items():
            mapping[name] = config or {}
            if not config:
                continue

    return mapping

def load(config_details):
    """Load the configuration from a working directory and a list of
    configuration files.  Files are loaded in order, and merged on top
    of each other to create the final configuration.

    Return a fully interpolated, extended and validated configuration.
    """
    # validate_config_version(config_details.config_files)

    processed_files = [
        process_config_file(config_file, config_details.environment)
        for config_file in config_details.config_files
    ]
    config_details = config_details._replace(config_files=processed_files)

    main_file = config_details.config_files[0]
    unikraft = load_mapping(
        config_details.config_files, 'get_unikraft', 'Unikraft', config_details.working_dir
    )
    architectures = load_mapping(
        config_details.config_files, 'get_architectures', 'Architecture', config_details.working_dir
    )
    platforms = load_mapping(
        config_details.config_files, 'get_platforms', 'Platform', config_details.working_dir
    )
    libraries = load_mapping(
        config_details.config_files, 'get_libraries', 'Library', config_details.working_dir
    )
    volumes = load_mapping(
        config_details.config_files, 'get_volumes', 'Volume', config_details.working_dir
    )

    return Config(main_file.version, unikraft, architectures, platforms, libraries, volumes)


def load_yaml(filename, encoding=None, binary=True):
    try:
        with io.open(filename, 'rb' if binary else 'r', encoding=encoding) as fh:
            return yaml.safe_load(fh)
    except (IOError, yaml.YAMLError, UnicodeDecodeError) as e:
        if encoding is None:
            # Sometimes the user's locale sets an encoding that doesn't match
            # the YAML files. Im such cases, retry once with the "default"
            # UTF-8 encoding
            return load_yaml(filename, encoding='utf-8-sig', binary=False)
        error_name = getattr(e, '__module__', '') + '.' + e.__class__.__name__
        raise ConfigurationError(u"{}: {}".format(error_name, e))
