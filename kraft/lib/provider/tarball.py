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

import htmllistparse

from .provider import LibraryProvider
from kraft.const import SEMVER_PATTERN
from kraft.const import TARBALL_SUPPORTED_EXTENSIONS
from kraft.logger import logger


def tarball_probe_remote_versions(source=None):
    versions = {}

    if source is None:
        return versions

    # Remove everything after the $ (start of variable)
    if '/$' in source:
        source = source[:source.index('$')]

    # Remove the filename
    else:
        for ext in TARBALL_SUPPORTED_EXTENSIONS:
            if source.endswith(ext):
                filename = source.split('/')[-1]
                source = source.replace(filename, '')
                break

    try:
        cwd, listings = htmllistparse.fetch_listing(source, timeout=30)

        for listing in listings:
            if listing.name.endswith(tuple(TARBALL_SUPPORTED_EXTENSIONS)):
                ver = SEMVER_PATTERN.search(listing.name)
                if ver is not None and ver.group(0) not in versions.keys():
                    versions[ver.group(0)] = listing.name

    except Exception as e:
        logger.warn(e)
        pass

    print(versions)

    return versions


class TarballLibraryProvider(LibraryProvider):

    @classmethod
    def is_type(cls, origin=None):
        if origin is None:
            return False

        for ext in TARBALL_SUPPORTED_EXTENSIONS:
            if origin.endswith(ext):
                return True

        return False

    def probe_remote_versions(self, source=None):
        if source is None:
            source = self.source

        return tarball_probe_remote_versions(source)

    def version_source_archive(self, varname=None):
        ver = SEMVER_PATTERN.search(self.source)
        source_archive = self.source.replace(ver.group(0), varname)
        return source_archive
