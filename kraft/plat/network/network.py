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
    _ip = None
    _mac = None
    _gateway = None
    _driver = None
    # _type = None
    _driver = None
    _bridge_name = None
    _pre_up = []
    _post_down = []

    @property
    def name(self):
        """
        This refers to the network name and is used to distinguish against
        other networks used on the target platform and within the unikraft
        specification.
        """
        return self._name

    @property
    def ip(self):
        """
        The desired IP address for the unikraft application on this network.
        """
        return self._ip

    @property
    def mac(self):
        """
        The desired MAC address for the unikraft application on this network.
        """
        return self._mac

    @property
    def gateway(self):
        """The gateway IP address for this network.
        """
        return self._gateway

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

    # @property
    # def type(self):
    #     """The network type represents the internal unikraft supported network
    #     stack.
    #     """
    #     return self._type

    @property
    def bridge_name(self):
        """
        The desired name of the bridge for this network.
        """
        return self._bridge_name

    @property
    def pre_up(self):
        """
        This is the user-defined script which is called before the networking
        stack is instantiated and is used to configure the network on behalf of
        the unikernel where internal support is insufficient.
        """
        return self._pre_up

    def append_pre_up(self, cmds=None):
        if isinstance(cmds, six.string_types):
            self._pre_up.extend([cmds])

        elif isinstance(cmds, list):
            self._pre_up.extend(cmds)

    @property
    def post_down(self):
        """
        The is the user-defined script which is called after the networking
        stack is destructed on the exit of a unikraft unikernel and is used to
        clean up networking artifacts (bridges, vifs, leases, etc.).
        """
        return self._post_down

    def append_post_down(self, cmds=[]):
        if isinstance(cmds, six.string_types):
            self._post_down.append(cmds)

        elif isinstance(cmds, list):
            self._post_down.extend(cmds)

    def __init__(self,
                 name,
                 ip,
                 mac,
                 gateway,
                 driver,
                 bridge_name,
                 pre_up,
                 post_down):
        self._name = name
        self._ip = ip
        self._mac = mac
        self._gateway = gateway
        self._driver = driver
        self._bridge_name = bridge_name

        if isinstance(pre_up, six.string_types):
            pre_up = [pre_up]
        if isinstance(post_down, six.string_types):
            post_down = [post_down]

        self._pre_up = pre_up
        self._post_down = post_down

    @classmethod  # noqa: C901
    def from_config(cls, name=None, config={}):
        interface = None
        ip = None
        mac = None
        gateway = None
        driver = DEFAULT_NETWORK_BRIDGE_DRIVER
        bridge_name = None
        pre_up = []
        post_down = []

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

            if 'bridge_name' in config:
                bridge_name = config['bridge_name']

            if 'pre_up' in config:
                pre_up = config['pre_up']

            if 'post_down' in config:
                post_down = config['post_down']

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

        if bridge_name is None:
            bridge_name = name

        return cls(
            name=name,
            ip=ip,
            mac=mac,
            gateway=gateway,
            driver=driver,
            bridge_name=bridge_name,
            pre_up=pre_up,
            post_down=post_down,
        )

    def __str__(self):
        text = "name:        %s\n" % self.name \
             + "pre_up:      %s\n" % (' '.join(self.pre_up)) \
             + "driver:      %s\n" % self.driver.type.name \
             + "bridge_name: %s\n" % self.bridge_name

        return text

    def repr(self):
        return {
            'pre_up': self.pre_up,
            'post_down': self.post_down
        }


class NetworkManager(object):
    _networks = []

    def __init__(self, network_base=[]):
        self._networks = network_base or []

    def add(self, network):
        if isinstance(network, Network):
            # Remove existing network with the same name so as to override
            for net in self._networks:
                if net.name == network.name:
                    logger.warning('Overriding existing network %s' % net.name)
                    self._networks.remove(net)
                    break

            self._networks.append(network)

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
