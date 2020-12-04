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
import re
from enum import Enum

import click
import six

from .app import Application
from .arch import Architecture
from .arch import ArchitectureManager
from .const import UK_GITHUB_CORE_FORMAT
from .const import UK_GITHUB_NAMING_FORMAT
from .error import UnknownVersionFormatError
from .lib import Library
from .lib import LibraryManager
from .manifest import ManifestVersionEquality
from .plat import Platform
from .plat import PlatformManager
from .unikraft import Unikraft
from kraft.const import UNIKRAFT_APPSDIR
from kraft.const import UNIKRAFT_ARCHSDIR
from kraft.const import UNIKRAFT_COREDIR
from kraft.const import UNIKRAFT_LIBSDIR
from kraft.const import UNIKRAFT_PLATSDIR
from kraft.const import UNIKRAFT_WORKDIR


class ComponentType(Enum):
    CORE = ( "core" , "unikraft"     , "unikraft"      , "UK_WORKDIR", Unikraft     , None                , UNIKRAFT_COREDIR  )  # noqa
    ARCH = ( "arch" , "architecture" , "architectures" , "UK_ARCHS",   Architecture , ArchitectureManager , UNIKRAFT_ARCHSDIR )  # noqa
    PLAT = ( "plat" , "platform"     , "platforms"     , "UK_PLATS",   Platform     , PlatformManager     , UNIKRAFT_PLATSDIR )  # noqa
    LIB  = ( "lib"  , "library"      , "libraries"     , "UK_LIBS",    Library      , LibraryManager      , UNIKRAFT_LIBSDIR  )  # noqa
    APP  = ( "app"  , "application"  , "applications"  , "UK_APPS",    Application  , None                , UNIKRAFT_APPSDIR  )  # noqa

    @property
    def format(self):
        if self.shortname == "core":
            return re.compile(UK_GITHUB_CORE_FORMAT)
        else:
            return re.compile(UK_GITHUB_NAMING_FORMAT % self.shortname)

    @property
    def shortname(self): return self.value[0]

    @property
    def name(self): return self.value[1]

    @property
    def plural(self): return self.value[2]

    def search(self, name):
        """
        Search determines whether the provided input `name` is of the
        repository naming format.  The method returns the usable name for the
        repository and thus the repository.
        """
        return self.format.search(name)

    @property
    def env(self): return self.value[3]

    @click.pass_context
    def localdir(ctx, self, name=None):
        # First check if there is a ./.unikraft directory present
        if self == ComponentType.CORE:
            localdir = os.path.join(
                ctx.obj.workdir, UNIKRAFT_WORKDIR, self.workdir
            )
        elif name is not None:
            localdir = os.path.join(
                ctx.obj.workdir, UNIKRAFT_WORKDIR, self.workdir, name
            )

        if os.path.exists(localdir):
            return localdir

        # Return the default location based on environmental variables
        if name is None:
            return ctx.obj.env.get(self.env)
        else:
            return os.path.join(ctx.obj.env.get(self.env), name)

    @property
    def cls(self): return self.value[4]

    @property
    def manager_cls(self): return self.value[5]

    @property
    def workdir(self): return self.value[6]


def str_to_component_type(name=None):
    for t in ComponentType.__members__.values():
        if name == t.shortname or (name == t.shortname + "s"):
            return t

    return None


def break_component_naming_format(name=None):
    if name is None or not isinstance(name, six.string_types):
        raise TypeError("name is not string")

    _type = None
    _name = None
    _eq = None
    _version = None

    # parse type and name: type-name or type/name
    if name.count("/") > 0:
        name_parts = name.split("/")
        _type = str_to_component_type(name_parts[0])
        if _type is None:
            _name = name_parts[-1]
            name = _name
        else:
            _name = "/".join(name_parts[1:])

    if name.count("-") > 0 and _type is None:
        name_parts = name.split("-")
        _type = str_to_component_type(name_parts[0])
        if _type is None:
            _name = name
        else:
            _name = "-".join(name_parts[1:])

    if name == "unikraft":
        _type = ComponentType.CORE
        _name = "unikraft"

    if _name is None:
        _name = name

    try:
        _name, _eq, _version = ManifestVersionEquality.split(_name)
    except UnknownVersionFormatError:
        pass

    return (_type, _name, _eq, _version)
