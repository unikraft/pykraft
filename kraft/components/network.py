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

import six
import ipaddress
import subprocess

from enum import Enum
from shutil import which

import kraft.utils as utils
from kraft.logger import logger

from kraft.errors import NetworkDriverError
from kraft.errors import InvalidBridgeName
from kraft.errors import DNSMASQCannotStartServer
from kraft.errors import NetworkBridgeUnsupported

BRCTL = "brctl"
# DNSMASQ = "dnsmasq"
DEFAULT_NETWORK_BRIDGE_DRIVER = "brctl"

class NetworkDriver(object):
    _name = None
    _type = None

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type
    
    def __init__(self, name=None, type=None):
        if name is not None:
            self._name = name
        else:
            self._name = NetworkDriver.generate_bridge_name()
        
        self._type = type
    
    def integrity_ok(self):
        return False

    def create_bridge(self, name=None, dry_run=False):
        raise NetworkDriverError("Creating a bridge is not possible with driver %s" % self.type)
    
    def add_vif(self, name=None):
        raise NetworkDriverError("Adding an interface is not possible with driver %s" % self.type)
    
    def remove_vif(self, name=None):
        raise NetworkDriverError("Removing an interface is not possible with driver %s" % self.type)
    
    def destroy_bridge(self, name=None):
        raise NetworkDriverError("Removing a bridge is not possible with driver %s" % self.type)
    
    def bridge_exists(self, name=None):
        raise NetworkDriverError("Checking for a bridge is not possible with driver %s" % self.type)
    
    def generate_bridge_name(self, prefix='virbr', max_tries=1024):
        suffix_i = 0
        new_name = None

        while suffix_i < max_tries:
            new_name = prefix + str(suffix_i)

            if not self.bridge_exists(new_name):
                return new_name

            suffix_i += 1

        raise KraftError("Max tries for bridge creation reached!")

class LinuxBRCTLDriver(NetworkDriver):
    def __init__(self, name, type):
        super(LinuxBRCTLDriver, self).__init__(name, type)
    
    def integrity_ok(self):
        return which(BRCTL) is not None

    def create_bridge(self, name=None, dry_run=False):
        if not self.integrity_ok():
            raise NetworkBridgeUnsupported(self.type.name)
        
        if name is None:
            name = self._name

        if self.bridge_exists(name):
            logger.warning("Bridge '%s' already exists!" % name)
            return True

        if name is not None and len(name) > 0:
            utils.execute([
                BRCTL, "addbr", name
            ], dry_run=dry_run)
        else:
            raise InvalidBridgeName(name)
        
        return True

    def destroy_bridge(self, name=None):
        if not self.integrity_ok():
            raise NetworkBridgeUnsupported(self.type.name)
        
        if name is None:
            name = self.name

        if name is not None and len(name) > 0:
            utils.execute([
                BRCTL, "delbr", name
            ])
        else:
            raise InvalidBridgeName(name)

    def bridge_exists(self, name=None):
        if not self.integrity_ok():
            raise NetworkBridgeUnsupported(self.type.name)

        process = subprocess.Popen([BRCTL, "show", name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        
        if err == b"can't get info No such device\n":
            return False
        
        return True

        

# class OVSDriver(NetworkDriver):

#     def __init__(self, name, type):
#         super(OVSDriver, self).__init__(name, type)
    
#     def integrity_ok(self):
#         return False
    
#     def create_bridge(self, name=None, dry_run=False):
#         pass
    
#     def add_vif(self, name=None):
#         pass
    
#     def remove_vif(self, name=None):
#         pass
    
#     def destroy_bridge(self, name=None):
#         pass
    
#     def bridge_exists(self, name=None):
#         pass

# class NetmapDriver(NetworkDriver):

#     def __init__(self, name, type):
#         super(NetmapDriver, self).__init__(name, type)
    
#     def integrity_ok(self):
#         return False
    
#     def create_bridge(self, name=None, dry_run=False):
#         pass
    
#     def add_vif(self, name=None):
#         pass
    
#     def remove_vif(self, name=None):
#         pass
    
#     def destroy_bridge(self, name=None):
#         pass
    
#     def bridge_exists(self, name=None):
#         pass

class NetworkDriverEnum(Enum):
    BRCTL   = ("brctl"  , LinuxBRCTLDriver)
    # OVS     = ("ovs"    , OVSDriver)
    # NETMAP  = ("netmap" , NetmapDriver)

    @property
    def name(self):
        return self.value[0]
    
    @property
    def cls(self):
        return self.value[1]

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
        """This refers to the network name and is used to distinguish against
        other networks used on the target platform and within the unikraft
        specification."""
        return self._name

    @property
    def ip(self):
        """The desired IP address for the unikraft application on this network.
        """
        return self._ip

    @property
    def mac(self):
        """The desired MAC address for the unikraft application on this network.
        """
        return self._mac

    @property
    def gateway(self):
        """The gateway IP address for this network."""
        return self._gateway

    @property
    def driver(self):
        """The network driver represents the mechanism by the which the network
        will operate under.  The network driver is responsible for creating,
        when necessary, the bridge and adding sany virtual network interfaces to
        the unikernel.  This is limited to a number of supported software-
        defined networking systems."""
        return self._driver

    # @property
    # def type(self):
    #     """The network type represents the internal unikraft supported network
    #     stack.
    #     """
    #     return self._type

    @property
    def bridge_name(self):
        """The desired name of the bridge for this network."""
        return self._bridge_name

    @property
    def pre_up(self):
        """This is the user-defined script which is called before the networking
        stack is instantiated and is used to configure the network on behalf of
        the unikernel where internal support is insufficient."""
        return self._pre_up

    def append_pre_up(self, cmds=None):
        if isinstance(cmds, six.string_types):
            self._pre_up.extend([cmds])

        elif isinstance(cmds, list):
            self._pre_up.extend(cmds)

    @property
    def post_down(self):
        """The is the user-defined script which is called after the networking
        stack is destructed on the exit of a unikraft unikernel and is used to
        clean up networking artifacts (bridges, vifs, leases, etc.)."""
        return self._post_down

    def append_post_down(self, cmds=[]):
        if isinstance(cmds, six.string_types):
            self._post_down.append(cmds)

        elif isinstance(cmds, list):
            self._post_down.extend(cmds)

    def __init__(self, name, ip, mac, gateway, driver, bridge_name, pre_up,
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
    
    @classmethod
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
                    member.name for _, member in NetworkDriverEnum.__members__.items()
                ]:
                driver = config['driver']

            if 'bridge_name' in config:
                bridge_name = config['bridge_name']
            
            if 'pre_up' in config:
                pre_up = config['pre_up']
            
            if 'post_down' in config:
                post_down = config['post_down']
    
        # Instantiate the driver
        for driver_name, member in NetworkDriverEnum.__members__.items():
            if member.name == driver:
                if interface == None:
                    interface = name

                driver = member.cls(
                    name=interface,
                    type=member
                )
                break
        
        if bridge_name is None:
            bridge_name = name
        
        return cls(
            name = name,
            ip = ip,
            mac = mac,
            gateway = gateway,
            driver = driver,
            bridge_name = bridge_name,
            pre_up = pre_up,
            post_down = post_down,
        )
    
    def __str__(self):
        text = "name:        %s\n" % self.name \
             + "pre_up:      %s\n" % (' '.join(self.pre_up)) \
             + "driver:      %s\n" % self.driver.type.name \
             + "bridge_name: %s\n" % self.bridge_name

        return text

class Networks(object):
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
            
        elif isinstance(network, Networks):
            for net in network.all():
                self.add(net)

    def get(self, key, default=None):
        for network in self._networks:
            if network.name == key:
                return network

    def all(self):
        return self._networks
    
    @classmethod
    def from_config(cls, config=None):
        networks = cls([])

        for net in config:
            networks.add(Network.from_config(net, config[net]))

        return networks

# def start_dnsmasq_server(bridge=None, listen_addr=None, ip_range=None, netmask=None, lease_time=None):
#     """Instantiate a new Dnsmasq server running as a user-space daemon."""

#     if ip_range is None:
#         raise DNSMASQCannotStartServer("No IP range provided")
    
#     if netmask is None:
#         netmask = "255.255.0.0"

#     ip_range_start, ip_range_end = ip_range.split(',')

#     if ip_range_start is None or ip_range_end is None:
#         raise DNSMASQCannotStartServer("Could not parse IP range, format is: a.b.c.d,w.x.y.z")
    
#     # We can figure out the listen address and increase the start IP.  This
#     # logic may not work in all circumstances, particularly if the netmask
#     # does not correspond to the IP range start.
#     if listen_addr is None:
#         listen_addr = ip_range_start
#         new_start = ipaddress.ip_network((ip_range_start, netmask), strict=False)
#         if new_start.num_addresses > 3:
#             ip_range_start = new_start[2]
#         else:
#             raise DNSMASQCannotStartServer("Could not assign a listen address based on provided netmask")

#     if lease_time is None:
#         lease_time = "12h"
    
#     cmd = [
#         DNSMASQ,
#         # "-d",
#         "--log-queries",
#         "--bind-interface",
#         ("--listen-address=%s" % listen_addr),
#         ("--dhcp-range=%s,%s,%s,%s" % (ip_range_start, ip_range_end, netmask, lease_time))
#     ]

#     if bridge is not None:
#         cmd.extend(('-i', bridge))

#     logger.info("Starting dnsmasq server...")
#     logger.debug('Running: %s' % ' '.join(cmd))

#     process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     return process
