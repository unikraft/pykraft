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
import six
import yaml

from collections import namedtuple
from cached_property import cached_property

from .version import SpecificationVersion
from .validation import validate_config_section
from .validation import validate_libraries_section
from .validation import validate_unikraft_section
from .validation import validate_top_level_string
from .validation import validate_against_config_schema
from .interpolation import interpolate_environment_variables
from .interpolation import interpolate_source_version

from kraft.types import RepositoryType

from kraft.errors import KraftError
from kraft.errors import KraftFileNotFound
from kraft.logger import logger

from kraft.constants import SUPPORTED_FILENAMES

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

        version_pattern = re.compile(r"^[0-9]+(\.\d+)?$")
        if not version_pattern.match(version):
            raise KraftError(
                'Specification "{}" in "{}" is invalid.'
                .format(version, self.filename))

        return SpecificationVersion(version)

    def get_name(self):
        return self.config.get('name', '')

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

    def get_volume(self, name):
        return self.get_volumes()[name]

    def get_volumes(self):
        return self.config.get('volumes', {})

    def get_network(self, name):
        return self.get_networks()[name]

    def get_networks(self):
        return self.config.get('networks', {})

class Config(namedtuple('_Config', 'specification name unikraft architectures platforms libraries volumes networks')):
    """
    :param specification: configuration version
    :type  specification: int

    :param name: name of the project
    :type  name: string

    :param unikraft: Unikraft's core configuration
    :type  unikraft: :class:`dict`

    :param architectures: Dictionary mapping architecture names to description dictionaries
    :type  architectures: :class:`dict`

    :param platforms: Dictionary mapping platform names to description dictionaries
    :type  platforms: :class:`dict`

    :param libraries: Dictionary mapping library names to description dictionaries
    :type  libraries: :class:`dict`

    :param volumes: Dictionary mapping volume names to description dictionaries
    :type  volumes: :class:`dict`

    :param networks: Dictionary mapping network names to description dictionaries
    :type  networks: :class:`dict`
    """

def get_project_name(workdir, project_name=None, environment=None):
    def normalize_name(name):
        return re.sub(r'[^-_a-z0-9]', '', name.lower())

    if not environment:
        environment = Environment.from_env_file(workdir)
        
    project_name = project_name or environment.get('KRAFT_PROJECT_NAME')
    
    if project_name:
        return normalize_name(project_name)

    project = os.path.basename(os.path.abspath(workdir))

    if project:
        return normalize_name(project)

    return 'default'

def process_top_level_string(config_file, config, environment, section, interpolate):
    validate_top_level_string(config_file, config, section)
    if interpolate and isinstance(config, dict):
        return interpolate_environment_variables(
            config_file.version,
            config,
            section,
            environment
            )
    else:
        return config

def process_unikraft(config_file, environment, interpolate):
    config = config_file.get_unikraft()
    validate_unikraft_section(config_file, config)
    if interpolate and isinstance(config, dict):
        return interpolate_environment_variables(
            config_file.version,
            config,
            "unikraft",
            environment
            )
    else:
        return config

def process_libraries(config_file, environment, interpolate):
    config = config_file.get_libraries()
    validate_libraries_section(config_file, config)
    if interpolate and isinstance(config, dict):
        return interpolate_environment_variables(
            config_file.version,
            config,
            "libraries",
            environment
            )
    else:
        return config

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

    processed_config['unikraft'] = process_unikraft(
        config_file,
        environment,
        interpolate,
    )
    processed_config['name'] = process_top_level_string(
        config_file,
        config_file.get_name(),
        'name',
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
    processed_config['libraries'] = process_libraries(
        config_file,
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
    processed_config['networks'] = process_config_section(
        config_file,
        config_file.get_networks(),
        'networks',
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
        attr = getattr(config_file, get_func)()
        if isinstance(attr, list):
            for name, config in getattr(config_file, get_func)().items():
                mapping[name] = config or {}
                if not config:
                    continue
        else:
            mapping = attr

    return mapping

def load(config_details):
    """Load the configuration from a working directory and a list of
    configuration files.  Files are loaded in order, and merged on top
    of each other to create the final configuration.

    Return a fully interpolated, extended and validated configuration.
    """

    processed_files = [
        process_config_file(config_file, config_details.environment)
        for config_file in config_details.config_files
    ]
    config_details = config_details._replace(config_files=processed_files)

    main_file = config_details.config_files[0]
    
    name = load_mapping(
        config_details.config_files,
        'get_name',
        'name',
        config_details.working_dir
    )

    if name is None or len(name) == 0:
        name = get_project_name(config_details.working_dir,  None, config_details.environment)

    unikraft = load_mapping(
        config_details.config_files, 'get_unikraft', 'unikraft', config_details.working_dir
    )

    # Account for syntax variation
    thought_source, thought_version = None, None
    
    if isinstance(unikraft, six.string_types):
        thought_source = unikraft
        unikraft = {}
    else:
        if 'source' in unikraft:
            thought_source = unikraft['source']
        if 'version' in unikraft:
            thought_version = unikraft['version']
        
    definite_source, definite_version = interpolate_source_version('unikraft', thought_source, thought_version, RepositoryType.CORE)
    unikraft['source'] = definite_source
    unikraft['version'] = definite_version
    
    architectures = load_mapping(
        config_details.config_files,
        'get_architectures',
        'architectures',
        config_details.working_dir
    )
    platforms = load_mapping(
        config_details.config_files,
        'get_platforms',
        'platforms',
        config_details.working_dir
    )
    libraries = load_mapping(
        config_details.config_files,
        'get_libraries',
        'libraries',
        config_details.working_dir
    )

    # Account for syntax variation
    for library in libraries:
        thought_source, thought_version = None, None
        
        if isinstance(libraries[library], str):
            thought_source = libraries[library]
            libraries[library] = {}
        else:
            if 'source' in libraries[library]:
                thought_source = libraries[library]['source']
            if 'version' in libraries[library]:
                thought_version = libraries[library]['version']
            
        definite_source, definite_version = interpolate_source_version(library, thought_source, thought_version, RepositoryType.LIB)
        libraries[library]['source'] = definite_source
        libraries[library]['version'] = definite_version

    volumes = load_mapping(
        config_details.config_files,
        'get_volumes',
        'volumes',
        config_details.working_dir
    )
    networks = load_mapping(
        config_details.config_files,
        'get_networks',
        'networks',
        config_details.working_dir
    )

    return Config(main_file.version, name, unikraft, architectures, platforms, libraries, volumes, networks)


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
        raise KraftError(u"{}: {}".format(error_name, e))
