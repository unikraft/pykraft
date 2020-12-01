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

import os
import six

from kraft.config import Config

from kraft.plat.volume import Volume
from kraft.plat.volume import VolumeManager
from kraft.plat.network import NetworkDriver
from kraft.plat.network import NetworkManager

from kraft.logger import logger

from kraft.error import RunnerError

import kraft.util as util


class Runner(object):
    _base_cmd = ''
    @property
    def base_cmd(self): return self._base_cmd

    _cmd = []
    @property
    def cmd(self): return self._cmd

    _platform = None
    @property
    def platform(self): return self._platform

    _volumes = {}
    @property
    def volumes(self): return self._volumes

    _networks = {}
    @property
    def networks(self): return self._networks

    _start_paused = False
    @property
    def start_paused(self): return self._start_paused

    _background = False
    @property
    def background(self): return self._background

    _unikernel = None
    @property
    def unikernel(self): return self._unikernel

    _architecture = None
    @property
    def architecture(self): return self._architecture

    _pre_up = []
    @property
    def pre_up(self): return self._pre_up

    _post_down = []
    @property
    def post_down(self): return self._post_down

    _arguments = None

    @property
    def arguments(self):
        if isinstance(self._arguments, six.string_types):
            return self._arguments
        elif isinstance(self._arguments, list):
            return ' '.join(self._arguments)
        else:
            return None

    _use_debug = False
    @property
    def use_debug(self): return self._use_debug

    def __init__(self, arguments=[], volumes=None, networks=None):
        self._arguments = arguments
        self._volumes = volumes or VolumeManager([])
        self._networks = networks or NetworkManager([])

    def add_initrd(self, initrd=None):
        if initrd:
            self._cmd.extend(('-i', initrd))

    def add_virtio_nic(self, virtio_nic=None):
        if virtio_nic:
            self._cmd.extend(('-n', virtio_nic))

    def add_bridge(self, bridge=None):
        if bridge:
            logger.info("Using networking bridge '%s'" % bridge)
            self._cmd.extend(('-b', bridge))

    def add_interface(self, interface=None):
        if interface:
            self._cmd.extend(('-V', interface))

    def add_virtio_raw(self, image=None):
        if image:
            self._cmd.extend(('-d', image))

    def add_virtio_qcow2(self, image=None):
        if image:
            self._cmd.extend(('-q', image))

    def add_virtio_9pfs(self, image=None):
        if image:
            self._cmd.extend(('-e', image))

    def open_gdb(self, port=None):
        if port and isinstance(port, int):
            self._cmd.extend(('-g', port))

    @property
    def use_debug(self):
        return self._use_debug

    @use_debug.setter
    def use_debug(self, flag=True):
        self._use_debug = flag

    def set_memory(self, memory=None):
        if memory and isinstance(memory, int):
            self._cmd.extend(('-m', memory))

    def set_cpu_sockets(self, cpu_sockets=None):
        if cpu_sockets and isinstance(cpu_sockets, int):
            self._cmd.extend(('-s', cpu_sockets))

    def set_cpu_cores(self, cpu_cores=None):
        if cpu_cores and isinstance(cpu_cores, int):
            self._cmd.extend(('-c', cpu_cores))

    @property
    def unikernel(self):
        unikernel = self._unikernel
        if self._use_debug:
            unikernel += UK_DBG_EXT

        return unikernel

    @unikernel.setter
    def unikernel(self, unikernel=None):
        if not unikernel or not os.path.exists(unikernel):
            raise RunnerError("Could not find unikernel: %s" % unikernel)

        self._unikernel = unikernel

    @property
    def architecture(self):
        return self._architecture

    @architecture.setter
    def architecture(self, arch):
        if arch:
            self._architecture = arch

    def execute(self, extra_args=None, background=False, paused=False, dry_run=False):
        raise RunnerError('Using undefined runner driver')

    def automount(self, dry_run=False):
        for vol in self.volumes.all():
            if vol.driver is VolumeDriver.VOL_INITRD:
                self.add_initrd(vol.source)

            if vol.driver is VolumeDriver.VOL_9PFS:
                source = vol.source

                # Extract tarball file systems
                if not dry_run and vol.source.lower().endswith(('.tgz', '.tar.gz', '.tar')):
                    source = tempfile.mkdtemp()
                    logger.debug('Extracting %s to %s...' % (vol.source, source))
                    tarball = tarfile.open(vol.source)
                    tarball.extractall(source)
                    tarball.close()

                self.add_virtio_9pfs(source)

            if vol.driver is VolumeDriver.VOL_RAW:
                self.add_virtio_raw(vol.source)

            if vol.driver is VolumeDriver.VOL_QCOW2:
                self.add_virtio_qcow2(vol.source)

    def autoconnect(self, dry_run=False):
        """Run the network's pre_up scripts and set up the bridge based on the
        relevant driver."""

        for net in self.networks.all():
            network_bridge = net.bridge_name

            if network_bridge:
                if not net.driver.bridge_exists(network_bridge):
                    net.driver.create_bridge(network_bridge, dry_run)
            else:
                network_bridge = net.driver.generate_bridge_name()

            self.add_bridge(network_bridge)

            env = {
                'KRAFT_NETWORK_NAME': net.name,
                'KRAFT_NETWORK_DRIVER': net.driver.type.name,
                'KRAFT_NETWORK_BRIDGE': network_bridge
            }

            env_str = []
            for var in env:
                env_str.append('%s=%s' % (var, env[var]))

            for cmd in net.pre_up:
                util.execute(cmd, env, dry_run)

    @property
    def pre_up(self):
        """This is the user-defined script which is called before the unikernel
        is instantiated and is used to configure the environment for the
        unikernel where internal support is insufficient."""
        return self._pre_up

    def append_pre_up(self, cmds=[]):
        if isinstance(cmds, six.string_types):
            self._pre_up.append(cmds)

        elif isinstance(cmds, list):
            self._pre_up.extend(cmds)

    @property
    def post_down(self):
        """The is the user-defined script which is called after the unikernel
        is destructed on the exit of a unikernel and is used to clean up the
        environment."""
        return self._post_down

    def append_post_down(self, cmds=[]):
        if isinstance(cmds, six.string_types):
            self._post_down.append(cmds)

        elif isinstance(cmds, list):
            self._post_down.extend(cmds)

    @classmethod
    def from_config(cls, config=None, runner_base=None):
        arguments = None
        if config and 'arguments' in config:
            arguments = config['arguments']
        elif runner_base is not None:
            arguments = runner_base.arguments

        if config and 'volumes' in config:
            volumes = VolumeManager.from_config(config['volumes'])
        else:
            volumes = VolumeManager([])

        if config and 'networks' in config:
            networks = NetworkManager.from_config(config['networks'])
        else:
            networks = NetworkManager([])

        # Override base with new configuration
        if runner_base is not None:
            runner_base.networks.add(networks)
            networks = runner_base.networks
            runner_base.volumes.add(volumes)
            volumes = runner_base.volumes

        runner = cls(
            arguments=arguments,
            networks=networks,
            volumes=volumes
        )

        if config and 'pre_up' in config:
            runner.append_pre_up(config['pre_up'])

        if config and 'post_down' in config:
            runner.append_post_down(config['post_down'])

        return runner

    def repr(self):
        config = {}

        if self.arguments is not None:
            config['arguments'] = self.arguments

        if self.volumes is not None and isinstance(self.volumes, VolumeManager):
            volumes_config = self.volumes.repr()
            if volumes_config is not None and len(volumes_config) > 0:
                config['volumes'] = volumes_config

        if self.networks is not None and isinstance(self.networks, NetworkManager):
            networks_config = self.networks.repr()
            if networks_config is not None and len(networks_config) > 0:
                config['networks'] = networks_config

        return config
