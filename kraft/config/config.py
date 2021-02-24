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

import io
import json
import os
import re
import sys
from collections import namedtuple

import six
import yaml
from cached_property import cached_property

from .environment import Environment
from .interpolation import interpolate_environment_variables
from .validation import validate_against_config_schema
from .version import SpecificationVersion
from kraft.const import KRAFT_SPEC_LATEST
from kraft.const import KRAFT_SPEC_V04
from kraft.const import SUPPORTED_FILENAMES
from kraft.error import CannotReadKraftfile
from kraft.error import KraftError
from kraft.error import KraftFileNotFound
from kraft.lib import LibraryManager
from kraft.logger import logger
from kraft.plat.network import NetworkManager
from kraft.plat.volume import VolumeManager
from kraft.target import TargetManager
from kraft.unikraft import Unikraft


class Config(object):
    """
    :param specification: configuration version
    :type  specification: int
    """
    _specification = None
    @property
    def specification(self): return self._specification

    @specification.setter
    def specification(self, specification=None): self._specification = specification

    """
    :param name: name of the project
    :type  name: string
    """
    _name = None
    @property
    def name(self): return self._name

    @name.setter
    def name(self, name=None): self._name = name

    """
    :param arguments: arguments of the component
    :type  arguments: string number
    """
    _arguments = None
    @property
    def arguments(self): return self._arguments
    @arguments.setter
    def arguments(self, arguments): self._arguments = arguments

    """
    :param before: before location for the component
    :type  before: string
    """
    _before = None
    @property
    def before(self): return self._before
    @before.setter
    def before(self, before): self._before = before

    """
    :param after: after location for the component
    :type  after: string
    """
    _after = None
    @property
    def after(self): return self._after
    @after.setter
    def after(self, after): self._after = after

    """
    :param unikraft: Unikraft's core configuration
    :type  unikraft: :class:`dict`
    """
    _unikraft = None
    @property
    def unikraft(self): return self._unikraft

    @unikraft.setter
    def unikraft(self, unikraft=None):
        if unikraft is None:
            return

        if isinstance(unikraft, dict):
            unikraft = Unikraft(**unikraft)

        elif not isinstance(unikraft, Unikraft):
            logger.warn("Cannot apply Unikraft to configuration")
            return

        self._unikraft = unikraft

    """
    :param targets: Dictionary mapping architecture and platform targets
    :type  targets: :class:`dict`
    """
    _targets = None
    @property
    def targets(self): return self._targets

    @targets.setter
    def targets(self, targets=None):
        if targets is None:
            return

        if isinstance(targets, dict):
            targets = TargetManager(**targets)

        elif not isinstance(targets, TargetManager):
            logger.warn("Cannot apply targets to configuration")
            return

        self._targets = targets

    """
    :param libraries: Dictionary mapping library names to description dictionaries
    :type  libraries: :class:`dict`
    """
    _libraries = None
    @property
    def libraries(self): return self._libraries

    @libraries.setter
    def libraries(self, libraries=None):
        if libraries is None:
            return

        if isinstance(libraries, dict):
            libraries = LibraryManager(**libraries)

        elif not isinstance(libraries, LibraryManager):
            logger.warn("Cannot apply Libraries to configuration")
            return

        self._libraries = libraries

    """
    :param volumes: Dictionary mapping of execution description dictionaries
    :type  volumes: :class:`dict`
    """
    _volumes = None
    @property
    def volumes(self): return self._volumes

    @volumes.setter
    def volumes(self, volumes=None):
        if volumes is None:
            return

        if isinstance(volumes, dict):
            volumes = VolumeManager(**volumes)

        elif not isinstance(volumes, VolumeManager):
            logger.warn("Cannot apply volumess to configuration")
            return

        self._volumes = volumes

    """
    :param networks: Dictionary mapping of execution description dictionaries
    :type  networks: :class:`dict`
    """
    _networks = None
    @property
    def networks(self): return self._networks

    @networks.setter
    def networks(self, networks=None):
        if networks is None:
            return

        if isinstance(networks, dict):
            networks = NetworkManager(**networks)

        elif not isinstance(networks, NetworkManager):
            logger.warn("Cannot apply networkss to configuration")
            return

        self._networks = networks

    def __init__(self, *args, **kwargs):
        self.specification = kwargs.get('specification', None)
        self.name = kwargs.get('name', None)
        self.arguments = kwargs.get('arguments', [])
        self.before = kwargs.get('before', None)
        self.after = kwargs.get('after', None)
        self.unikraft = kwargs.get('unikraft', None)
        self.targets = kwargs.get('targets', TargetManager([]))
        self.libraries = kwargs.get('libraries', LibraryManager({}))
        self.volumes = kwargs.get('volumes', VolumeManager({}))
        self.networks = kwargs.get('networks', NetworkManager({}))

    def repr(self):
        ret = {}
        for k in self.__dict__.keys():
            v = getattr(self, k[1:])
            if isinstance(v, (six.string_types, dict, list)):
                ret[k[1:]] = v
            elif v is not None and hasattr(v, 'repr'):
                ret[k[1:]] = v.repr()

        return ret

    def __repr__(self):
        return json.dumps(self.repr())


class ConfigDetails(namedtuple(
        '_ConfigDetails', [
            'working_dir',
            'config_files',
            'environment',
        ])):
    """
    :param working_dir: the directory to use for relative paths in the config
    :type  working_dir: string
    :param config_files: list of configuration files to load
    :type  config_files: list of :class:`KraftFile`
     """
    def __new__(cls, working_dir, config_files, environment=None):
        if environment is None:
            environment = Environment.from_env_file(working_dir)
        return super(ConfigDetails, cls).__new__(
            cls, working_dir, config_files, environment
        )


class KraftFile(namedtuple(
        '_KraftFile', [
            'filename',
            'config'
        ])):
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
            return KRAFT_SPEC_LATEST

        version = str(self.config['specification'])

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

    def get_arguments(self):
        return self.config.get('arguments', None)

    def get_targets(self):
        return self.config.get('targets', [])

    def get_libraries(self):
        return self.config.get('libraries', {})

    def get_before(self):
        return self.config.get('before', None)

    def get_after(self):
        return self.config.get('after', None)

    def get_volumes(self):
        return self.config.get('volumes', {})

    def get_networks(self):
        return self.config.get('networks', {})


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


def process_kraftfile(kraftfile, environment, service_name=None, interpolate=True):
    if kraftfile.config is None:
        return kraftfile

    validate_against_config_schema(kraftfile)

    processed_config = dict()
    processed_config['unikraft'] = interpolate_environment_variables(
        kraftfile.version,
        kraftfile.get_unikraft(),
        "unikraft",
        environment
    )

    processed_config['name'] = kraftfile.get_name()

    if kraftfile.version == KRAFT_SPEC_V04:
        processed_config['arguments'] = None

        architectures = interpolate_environment_variables(
            kraftfile.version,
            kraftfile.config.get('architectures', {}),
            "architectures",
            environment
        )

        platforms = interpolate_environment_variables(
            kraftfile.version,
            kraftfile.config.get('platforms', {}),
            "platforms",
            environment
        )

        targets = list()

        # Naively (and this is why there is an update from v0.4 to v0.5) create
        # a list of targets based on iterating over architectures and platforms
        for arch in architectures:
            for plat in platforms:
                targets.append({
                    'architecture': arch,
                    'platform': plat
                })

        processed_config['targets'] = targets

        # Bring the network and volume directives from the run directive into
        # their own
        run = interpolate_environment_variables(
            kraftfile.version,
            kraftfile.config.get('run', {}),
            "run",
            environment
        )

        if 'networks' in run:
            processed_config['networks'] = run['networks']
        if 'volumes' in run:
            processed_config['volumes'] = run['volumes']

    elif kraftfile.version > KRAFT_SPEC_V04:
        processed_config['arguments'] = kraftfile.get_arguments()
        processed_config['before'] = kraftfile.get_before()
        processed_config['after'] = kraftfile.get_after()
        processed_config['targets'] = interpolate_environment_variables(
            kraftfile.version,
            kraftfile.get_targets(),
            "targets",
            environment
        )
        processed_config['networks'] = interpolate_environment_variables(
            kraftfile.version,
            kraftfile.get_networks(),
            "networks",
            environment
        )
        processed_config['volumes'] = interpolate_environment_variables(
            kraftfile.version,
            kraftfile.get_volumes(),
            "volumes",
            environment
        )

    processed_config['libraries'] = interpolate_environment_variables(
        kraftfile.version,
        kraftfile.get_libraries(),
        "libraries",
        environment
    )

    kraftfile = kraftfile._replace(config=processed_config)
    return kraftfile


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
        logger.warning("Found multiple config files with supported names: %s", ", ".join(candidates))
        logger.warning("Using %s", winner)

    return [os.path.join(path, winner)]


def find_config(base_dir, filenames, environment, override_dir=None):
    if filenames == ['-']:
        return ConfigDetails(
            os.path.abspath(override_dir) if override_dir else os.getcwd(),
            [KraftFile(None, yaml.safe_load(sys.stdin))],
            environment
        )

    if filenames:
        filenames = [os.path.join(base_dir, f) for f in filenames]
    else:
        filenames = get_default_config_files(base_dir)

    logger.debug("Using configuration files: %s" % (",".join(filenames)))
    return ConfigDetails(
        override_dir if override_dir else os.path.dirname(filenames[0]),
        [KraftFile.from_filename(f) for f in filenames],
        environment
    )


def load_mapping(config_files, get_func, entity_type, working_dir=None):
    mapping = None

    for config_file in config_files:
        if config_file.config is not None:
            attr = getattr(config_file, get_func)()
            if isinstance(attr, list):
                if mapping is None:
                    mapping = []
                for config in attr:
                    mapping.append(config)
            elif isinstance(attr, dict):
                if mapping is None:
                    mapping = {}
                for name, config in getattr(config_file, get_func)().items():
                    mapping[name] = config or {}
                    if not config:
                        continue
            else:
                mapping = attr

    return mapping


def load_config(config_details):
    """Load the configuration from a working directory and a list of
    configuration files.  Files are loaded in order, and merged on top
    of each other to create the final configuration.
    Return a fully interpolated, extended and validated configuration.
    """

    processed_files = [
        process_kraftfile(config_file, config_details.environment)
        for config_file in config_details.config_files
    ]
    config_details = config_details._replace(config_files=processed_files)

    main_file = config_details.config_files[0]

    if main_file.config is None:
        raise CannotReadKraftfile(main_file.filename)

    name = load_mapping(
        config_details.config_files,
        'get_name',
        'name',
        config_details.working_dir
    )

    if name is None or len(name) == 0:
        name = get_project_name(config_details.working_dir,  None, config_details.environment)

    unikraft = load_mapping(
        config_details.config_files,
        'get_unikraft',
        'unikraft',
        config_details.working_dir
    )
    arguments = load_mapping(
        config_details.config_files,
        'get_arguments',
        'arguments',
        config_details.working_dir
    )
    before = load_mapping(
        config_details.config_files,
        'get_before',
        'before',
        config_details.working_dir
    )
    after = load_mapping(
        config_details.config_files,
        'get_after',
        'after',
        config_details.working_dir
    )
    targets = load_mapping(
        config_details.config_files,
        'get_targets',
        'targets',
        config_details.working_dir
    )
    libraries = load_mapping(
        config_details.config_files,
        'get_libraries',
        'libraries',
        config_details.working_dir
    )
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

    if isinstance(unikraft, six.string_types):
        core = Unikraft(
            version=unikraft
        )
    else:
        core = Unikraft(**unikraft)

    return Config(
        specification=main_file.version,
        name=name,
        arguments=arguments,
        before=before,
        after=after,
        unikraft=core,
        targets=TargetManager(targets, core),
        libraries=LibraryManager(libraries),
        volumes=VolumeManager(volumes),
        networks=NetworkManager(networks),
    )


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
