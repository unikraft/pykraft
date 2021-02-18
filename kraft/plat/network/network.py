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

import six

from .driver import NetworkDriverTypes
from kraft.logger import logger


# DNSMASQ = "dnsmasq"
DEFAULT_NETWORK_BRIDGE_DRIVER = "brctl"


class Network(object):
    _name = None

    @property
    def name(self):
        """
        This refers to the network name and is used to distinguish against
        other networks used on the target platform and within the unikraft
        specification.
        """
        return self._name

    _ip = None

    @property
    def ip(self):
        """
        The desired IP address for the unikraft application on this network.
        """
        return self._ip

    _mac = None

    @property
    def mac(self):
        """
        The desired MAC address for the unikraft application on this network.
        """
        return self._mac

    _gateway = None

    @property
    def gateway(self):
        """The gateway IP address for this network.
        """
        return self._gateway

    _driver = None

    @property
    def driver(self):
        """
        The network driver represents the mechanism by the which the network
        will operate under.  The network driver is responsible for creating,
        when necessary, the bridge and adding sany virtual network interfaces to
        the unikernel.  This is limited to a number of supported software-
        defined networking systems.
        """
        return self._driver

    _bridge = None

    @property
    def bridge(self):
        """
        The desired name of the bridge for this network.
        """
        return self._bridge

    _before = []

    @property
    def before(self):
        """
        This is the user-defined script which is called before the networking
        stack is instantiated and is used to configure the network on behalf of
        the unikernel where internal support is insufficient.
        """
        return self._before

    def append_before(self, cmds=None):
        if isinstance(cmds, six.string_types):
            self._before.extend([cmds])

        elif isinstance(cmds, list):
            self._before.extend(cmds)

    _after = []

    @property
    def after(self):
        """
        The is the user-defined script which is called after the networking
        stack is destructed on the exit of a unikraft unikernel and is used to
        clean up networking artifacts (bridges, vifs, leases, etc.).
        """
        return self._after

    def append_after(self, cmds=[]):
        if isinstance(cmds, six.string_types):
            self._after.append(cmds)

        elif isinstance(cmds, list):
            self._after.extend(cmds)

    def __init__(self, *args, **kwargs):
        self._name = kwargs.get("name", None)
        self._ip = kwargs.get("ip", None)
        self._mac = kwargs.get("mac", None)
        self._gateway = kwargs.get("gateway", None)
        self._driver = kwargs.get("driver", None)
        self._bridge = kwargs.get("bridge", None)

        before = kwargs.get("before", None)
        after = kwargs.get("after", None)

        if isinstance(before, six.string_types):
            before = [before]
        if isinstance(after, six.string_types):
            after = [after]

        self._before = before
        self._after = after

    @classmethod  # noqa: C901
    def from_config(cls, name=None, config={}):
        interface = None
        ip = None
        mac = None
        gateway = None
        driver = DEFAULT_NETWORK_BRIDGE_DRIVER
        bridge = None
        before = []
        after = []

        if not isinstance(config, bool):
            if 'name' in config:
                name = config['name']

            if 'interface' in config:
                interface = config['interface']

            if 'ip' in config:
                ip = config['ip']

            if 'mac' in config:
                mac = config['mac']

            if 'gateway' in config:
                gateway = config['gateway']

            if 'driver' in config \
                and config['driver'] in [
                    member.name for _, member in NetworkDriverTypes.__members__.items()]:
                driver = config['driver']

            if 'bridge' in config:
                bridge = config['bridge']

            if 'before' in config:
                before = config['before']

            if 'after' in config:
                after = config['after']

        # Instantiate the driver
        for driver_name, member in NetworkDriverTypes.__members__.items():
            if member.name == driver:
                if interface is None:
                    interface = name

                driver = member.cls(
                    name=interface,
                    type=member
                )
                break

        if bridge is None:
            bridge = name

        return cls(
            name=name,
            ip=ip,
            mac=mac,
            gateway=gateway,
            driver=driver,
            bridge=bridge,
            before=before,
            after=after,
        )

    def __str__(self):
        text = "name:   %s\n" % self.name \
             + "before: %s\n" % (' '.join(self.before)) \
             + "driver: %s\n" % self.driver.type.name \
             + "bridge: %s\n" % self.bridge

        return text

    def repr(self):
        config = {}
        if self.ip is not None:
            config['ip'] = self.ip
        if self.mac is not None:
            config['mac'] = self.mac
        if self.gateway is not None:
            config['gateway'] = self.gateway
        if self.driver is not None:
            config['driver'] = self.driver
        if self.bridge is not None:
            config['bridge'] = self.bridge
        if self.before is not None:
            config['before'] = self.before
        if self.after is not None:
            config['after'] = self.after
        return config


class NetworkManager(object):
    _networks = []

    def __init__(self, network_base=[]):
        self._networks = []

        if isinstance(network_base, dict):
            for network in network_base.keys():
                self.add(Network(
                    name=network,
                    **network_base[network]
                ))

        elif isinstance(network_base, list):
            for network in network_base:
                self.add(network)

    def add(self, network):
        if isinstance(network, Network):
            # Remove existing network with the same name so as to override
            for net in self._networks:
                if net.name == network.name:
                    logger.warning('Overriding existing network %s' % net.name)
                    self._networks.remove(net)
                    break

            self._networks.append(network)

        elif isinstance(network, dict):
            self._networks.add(Network(**network))

        elif isinstance(network, NetworkManager):
            for net in network.all():
                self.add(net)

    def get(self, key, default=None):
        for network in self._networks:
            if network.name == key:
                return network

        return default

    def all(self):
        return self._networks

    @classmethod
    def from_config(cls, config=None):
        networks = cls([])

        for net in config:
            networks.add(Network.from_config(net, config[net]))

        return networks

    def repr(self):
        config = {}

        for network in self.all():
            config[network.name] = network.repr()

        return config
