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
from __future__ import absolute_import
from __future__ import unicode_literals

import htmllistparse

from .provider import Provider
from kraft.constants import SEMVER_PATTERN
from kraft.constants import TARBALL_SUPPORTED_EXTENSIONS


def tarball_probe_remote_versions(source=None):
    versions = {}

    if source is None:
        return versions

    # Remove last filename in URL in attempt to retrieve the index of the
    # directory
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

    except Exception:
        pass

    return versions


class TarballProvider(Provider):

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
