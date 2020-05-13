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
import six
import tarfile
import tempfile
import platform
import subprocess
from enum import Enum

import kraft.utils as utils
from kraft.logger import logger
from kraft.errors import ExecutorError

from kraft.components.volume import Volume
from kraft.components.volume import Volumes
from kraft.components.volume import VolumeDriver
from kraft.components.network import Network
from kraft.components.network import Networks

from kraft.constants import UK_DBG_EXT

WHICH='which'
class Executor(object):
    _base_cmd = ''
    _cmd = []
    _platform = None
    _volumes = {}
    _networks = {}
    _start_paused = False
    _background = False
    _unikernel = None
    _architecture = None
    _pre_up = []
    _post_down = []
    _arguments = None
    _use_debug = False

    @property
    def volumes(self):
        return self._volumes

    @property
    def networks(self):
        return self._networks

    @property
    def arguments(self):
        if isinstance(self._arguments, six.string_types):
            return self._arguments
        elif isinstance(self._arguments, list):
            return ' '.join(self._arguments)
        else:
            return None

    def __init__(self, arguments=[], volumes=None, networks=None):
        self._arguments = arguments
        self._volumes = volumes or Volumes([])
        self._networks = networks or Networks([])
    
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

    @staticmethod
    def which(cmd):
        try:
            cmd_list = [WHICH, cmd]
            location = subprocess.run(cmd_list, check=True, capture_output=True)
            cmd_path = location.stdout.decode().strip()
        except:
            raise ExecutorError("Could not find %s" % cmd)

        return [cmd_path]

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
            raise ExecutorError("Could not find unikernel: %s" % unikernel)

        self._unikernel = unikernel

    @property
    def architecture(self):
        return self._architecture
    
    @architecture.setter
    def architecture(self, arch):
        if arch:
            self._architecture = arch

    def execute(self, extra_args=None, background=False, paused=False, dry_run=False):
        raise ExecutorError('Using undefined executor driver')
    
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
                utils.execute(cmd, env, dry_run)

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
    def from_config(cls, ctx, config=None, executor_base=None):
        assert ctx is not None, "ctx is undefined"
        
        arguments = None
        if config and 'arguments' in config:
            arguments = config['arguments']
        elif executor_base is not None:
            arguments = executor_base.arguments

        if config and 'volumes' in config:
            volumes = Volumes.from_config(ctx.workdir, config['volumes'])
        else:
            volumes = Volumes([])

        if config and 'networks' in config:
            networks = Networks.from_config(config['networks'])
        else:
            networks = Networks([])

        # Override base with new configuration
        if executor_base is not None:
            executor_base.networks.add(networks)
            networks = executor_base.networks
            executor_base.volumes.add(volumes)
            volumes = executor_base.volumes

        executor = cls(
            arguments=arguments,
            networks=networks,
            volumes=volumes
        )

        if config and 'pre_up' in config:
            executor.append_pre_up(config['pre_up'])
        
        if config and 'post_down' in config:
            executor.append_post_down(config['post_down'])

        return executor

class LinuxExecutor(Executor):
    _base_cmd = ''

    def add_initrd(self, initrd=None):
        pass # noop
        
    def add_virtio_nic(self, virtio_nic=None):
        pass # noop
        
    def add_bridge(self, bridge=None):
        pass # noop
        
    def add_interface(self, interface=None):
        pass # noop
        
    def add_virtio_raw(self, image=None):
        pass # noop
        
    def add_virtio_qcow2(self, image=None):
        pass # noop
        
    def add_virtio_9pfs(self, image=None):
        pass # noop
        
    def open_gdb(self, port=None):
        pass # noop
        
    def set_memory(self, memory=None):
        pass # noop
        
    # TODO: Pin CPUs with isolcpus or taskset
    def set_cpu_sockets(self, cpu_sockets=None):
        pass # noop
        
    # TODO: Pin CPUs with isolcpus or taskset
    def set_cpu_cores(self, cpu_cores=None):
        pass # noop
        
    def execute(self, extra_args=None, background=False, paused=False, dry_run=False):
        logger.debug("Executing on Linux...")

        cmd = [
            self.unikernel
        ]

        if self.arguments:
            cmd.append(self.arguments)

        if extra_args:
            cmd.extend(extra_args)

        for pre_up_cmd in self._pre_up:
            utils.execute(pre_up_cmd, dry_run=dry_run)

        cmd = list(map(str, cmd))
        logger.debug('Running: %s' % ' '.join(cmd))

        if not dry_run:
            process = subprocess.Popen(cmd)

            try:
                process.wait()

            except KeyboardInterrupt:
                try:
                    process.terminate()
                except OSError:
                    pass
                process.wait()

        for post_down_cmd in self._post_down:
            utils.execute(post_down_cmd, dry_run=dry_run)

# TODO: Container runtime
# RUNC_GUEST='runc'
# class ContainerExecutor(Execeutor):
#     pass

QEMU_GUEST='qemu-guest'

class KVMExecutor(Executor):
    def execute(self, extra_args=None, background=False, paused=False, dry_run=False):
        logger.debug("Executing on KVM...")

        self._cmd.extend(('-k', self.unikernel))

        if background:
            self._cmd.append('-X')
        if paused:
            self._cmd.append('-P')
        if dry_run:
            self._cmd.append('-D')
        if extra_args:
            self._cmd.extend(('-a', ' '.join(extra_args)))
        
        self.automount(dry_run)
        self.autoconnect(dry_run)

        if self.architecture == "x86_64":
            self._cmd.extend(('-t', 'x86pc'))
        elif self.architecture == "arm64":
            self._cmd.extend(('-t', 'arm64v'))
        
        if platform.machine() != self.architecture:
            self._cmd.append('-W')

        if self.arguments:
            self._cmd.extend(('-a', self.arguments))
        
        cmd = self.which(QEMU_GUEST)
        cmd.extend(self._cmd)

        for pre_up_cmd in self._pre_up:
            utils.execute(pre_up_cmd, dry_run=dry_run)

        cmd = list(map(str, cmd))
        logger.debug('Running: %s' % ' '.join(cmd))

        if not dry_run:
            process = subprocess.Popen(cmd)

            try:
                process.wait()

            except KeyboardInterrupt:
                try:
                    process.terminate()
                except OSError:
                    pass
                process.wait()

        for post_down_cmd in self._post_down:
            utils.execute(post_down_cmd, dry_run=dry_run)
        
XEN_GUEST='xen-guest'
class XenExecutor(Executor):
    def execute(self, extra_args=None, background=False, paused=False, dry_run=False):
        logger.debug("Executing on Xen...")

        self._cmd.extend(('-k', self.unikernel))

        if background:
            self._cmd.append('-X')
        if paused:
            self._cmd.append('-P')
        if dry_run:
            self._cmd.append('-D')
        if extra_args:
            self._cmd.extend(('-a', ' '.join(extra_args)))
        
        self.automount(dry_run)
        self.autoconnect(dry_run)
        
        if self.arguments:
            self._cmd.extend(('-a', self.arguments))
        
        cmd = self.which(XEN_GUEST)
        cmd.extend(self._cmd)

        for pre_up_cmd in self._pre_up:
            utils.execute(pre_up_cmd, dry_run=dry_run)

        cmd = list(map(str, cmd))
        logger.debug('Running: %s' % ' '.join(cmd))

        if not dry_run:
            process = subprocess.Popen(cmd)

            try:
                process.wait()

            except KeyboardInterrupt:
                try:
                    process.terminate()
                except OSError:
                    pass
                process.wait()

        for post_down_cmd in self._post_down:
            utils.execute(post_down_cmd, dry_run=dry_run)

class ExecutorDriverEnum(Enum):
    XEN    = ("xen"    , XenExecutor)
    KVM    = ("kvm"    , KVMExecutor)
    LINUXU = ("linuxu" , LinuxExecutor)

    @property
    def name(self):
        return self.value[0]
    
    @property
    def cls(self):
        return self.value[1]
