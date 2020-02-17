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

import ipaddress
import subprocess

from enum import Enum
from shutil import which

import kraft.utils as utils
from kraft.logger import logger

from kraft.errors import InvalidBridgeName
from kraft.errors import DNSMASQCannotStartServer
from kraft.errors import KraftNetworkBridgeUnsupported

BRCTL = "brctl"
DNSMASQ = "dnsmasq"
DEFAULT_NETWORK_BRIDGE_DRIVER = "brctl"

class BridgeDriver(object):
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
            self._name = BridgeDriver.generate_bridge_name()
        
        self._type = type
    
    def check_driver_integrity(self):
        return False

    def create(self, name=None):
        raise NetworkBridgeError("Creating a bridge is not possible with driver %s" % self.type)
    
    def add_vif(self, name=None):
        raise NetworkBridgeError("Adding an interface is not possible with driver %s" % self.type)
    
    def remove_vif(self, name=None):
        raise NetworkBridgeError("Removing an interface is not possible with driver %s" % self.type)
    
    def destroy(self, name=None):
        raise NetworkBridgeError("Removing a bridge is not possible with driver %s" % self.type)
    
    def exists(self, name=None):
        raise NetworkBridgeError("Checking for a bridge is not possible with driver %s" % self.type)
    
    @classmethod
    def generate_bridge_name(self, prefix='virbr'):
        return None

class LinuxBRCTLDriver(BridgeDriver):
    def __init__(self, name, type):
        super(LinuxBRCTLDriver, self).__init__(name, type)
    
    def check_driver_integrity(self):
        return which(BRCTL) is not None

    def create(self, name=None):
        if not self.check_driver_integrity():
            raise KraftNetworkBridgeUnsupported(self.type.name)
        
        if name is None:
            name = self.name

        if name is not None and len(name) > 0:
            utils.execute([
                BRCTL, "addbr", name
            ])
        else:
            raise InvalidBridgeName(name)

    def destroy(self, name=None):
        if not self.check_driver_integrity():
            raise KraftNetworkBridgeUnsupported(self.type.name)
        
        if name is None:
            name = self.name

        if name is not None and len(name) > 0:
            utils.execute([
                BRCTL, "delbr", name
            ])
        else:
            raise InvalidBridgeName(name)

    def exists(self, name=None):
        if not self.check_driver_integrity():
            raise KraftNetworkBridgeUnsupported(self.type.name)
        
        process = subprocess.Popen([BRCTL, "show", name])
        process.communicate()[0]
        return process.returncode == 0

# class OVSDriver(BridgeDriver):

#     def __init__(self, name, type):
#         super(OVSDriver, self).__init__(name, type)
    
#     def check_driver_integrity(self):
#         return False
    
#     def create(self, name=None):
#         pass
    
#     def add_vif(self, name=None):
#         pass
    
#     def remove_vif(self, name=None):
#         pass
    
#     def destroy(self, name=None):
#         pass
    
#     def exists(self, name=None):
#         pass

# class NetmapDriver(BridgeDriver):

#     def __init__(self, name, type):
#         super(NetmapDriver, self).__init__(name, type)
    
#     def check_driver_integrity(self):
#         return False
    
#     def create(self, name=None):
#         pass
    
#     def add_vif(self, name=None):
#         pass
    
#     def remove_vif(self, name=None):
#         pass
    
#     def destroy(self, name=None):
#         pass
    
#     def exists(self, name=None):
#         pass

class BridgeDriverEnum(Enum):
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
    _bridge = None
    _ip = None
    _mac = None
    _gateway = None
    _driver = None
    _use_dhcp = False

    @property
    def name(self):
        return self._name

    @property
    def bridge(self):
        return self._bridge
    @property
    def ip(self):
        return self._ip
    @property
    def mac(self):
        return self._mac
    @property
    def gateway(self):
        return self._gateway

    def __init__(self, name, bridge, ip, mac, gateway, use_dhcp):
        self._name = name
        self._bridge = bridge
        self._ip = ip
        self._mac = mac
        self._gateway = gateway
        self._use_dhcp = use_dhcp
    
    @classmethod
    def from_config(cls, name=None, config={}):
        if 'name' in config:
            name = config['name']
        
        bridge = None
        if 'bridge' in config:
            bridge = config['bridge']
        
        ip = None
        if 'ip' in config:
            ip = config['ip']
        
        mac = None
        if 'mac' in config:
            mac = config['mac']
        
        gateway = None
        if 'gateway' in config:
            gateway = config['gateway']
        
        use_dhcp = False
        if 'dhcp' in config and isinstance(config['dhcp'], bool):
            use_dhcp = config['dhcp']
        
        # Determine bridge driver
        bridge_driver = DEFAULT_NETWORK_BRIDGE_DRIVER
        if 'bridge_driver' in config \
        and config['bridge_driver'] in [member.name for _, member in BridgeDriverEnum.__members__.items()]:
            bridge_driver = config['bridge_driver']

        # Instantiate the driver
        for driver_name, member in BridgeDriverEnum.__members__.items():
            if member.name == bridge_driver:
                bridge = member.cls(
                    name=bridge,
                    type=member
                )
                break
        
        return cls(
            name = name,
            bridge = bridge,
            ip = ip,
            mac = mac,
            gateway = gateway,
            use_dhcp = use_dhcp
        )
    
    def generate_mac(self):
        pass
    
    def determine_ip(self):
        pass

class Networks(object):
    _networks = []

    def __init__(self, network_base=[]):
        self._networks = network_base or []

    def add(self, network):
        self._networks.append(network)

    def get(self, key, default=None):
        for network in self._networks:
            if getattr(network, key) == value:
                return network

    def all(self):
        return self._networks
    
    @classmethod
    def from_config(cls, config=None):
        networks = cls([])

        for net in config:
            networks.add(Network.from_config(net, config[net]))

        return networks

def start_dnsmasq_server(bridge=None, listen_addr=None, ip_range=None, netmask=None, lease_time=None):
    """Instantiate a new Dnsmasq server running as a user-space daemon."""
    
    if bridge is None:
        raise DNSMASQCannotStartServer("No bridge provided")

    if ip_range is None:
        raise DNSMASQCannotStartServer("No IP range provided")
    
    if netmask is None:
        netmask = "255.255.0.0"

    ip_range_start, ip_range_end = ip_range.split(',')

    if ip_range_start is None or ip_range_end is None:
        raise DNSMASQCannotStartServer("Could not parse IP range, format is: a.b.c.d,w.x.y.z")
    
    # We can figure out the listen address and increase the start IP.  This
    # logic may not work in all circumstances, particularly if the netmask
    # does not correspond to the IP range start.
    if listen_addr is None:
        listen_addr = ip_range_start
        new_start = ipaddress.ip_network((ip_range_start, netmask), strict=False)
        if new_start.num_addresses > 3:
            ip_range_start = new_start[2]
        else:
            raise DNSMASQCannotStartServer("Could not assign a listen address based on provided netmask")

    if lease_time is None:
        lease_time = "12h"
    
    cmd = [
        DNSMASQ,
        "-i", bridge,
        "-d",
        "--log-queries",
        "--bind-interface",
        ("--listen-address=%s" % listen_addr),
        ("--dhcp-range=%s,%s,%s,%s" % (ip_range_start, ip_range_end, netmask, lease_time))
    ]
    logger.info("Starting dnsmasq server...")
    return subprocess.Popen(cmd)
