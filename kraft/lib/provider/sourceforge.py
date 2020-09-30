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

import feedparser

from .tarball import TarballLibraryProvider
from kraft.const import SEMVER_PATTERN
from kraft.const import SOURCEFORGE_DOWNLOAD
from kraft.const import SOURCEFORGE_PROJECT_FEED
from kraft.const import SOURCEFORGE_PROJECT_NAME
from kraft.const import TARBALL_SUPPORTED_EXTENSIONS


def sourceforge_probe_remote_versions(source=None):
    """
    List known versions of a project on SourceForge.

    Args:
        source:  The remote source on SourceForge.

    Returns:
        Dictionary of versions and their url.

    """
    versions = {}
    project_name = SOURCEFORGE_PROJECT_NAME.search(source)

    if project_name is None:
        return versions

    project_name = project_name.group(1)
    feed = feedparser.parse(SOURCEFORGE_PROJECT_FEED % project_name)

    for entry in feed.entries:
        url_parts = entry.links[0].href

        if url_parts.endswith(SOURCEFORGE_DOWNLOAD):
            url_parts = url_parts[:-len(SOURCEFORGE_DOWNLOAD)]

        filename = url_parts.split('/')[-1]

        for suffix in TARBALL_SUPPORTED_EXTENSIONS:
            if filename.endswith(suffix):
                filename = filename[:-len(suffix)]

        semver = SEMVER_PATTERN.search(filename)
        if semver is not None:
            versions[semver.group(0)] = entry.links[0].href

    return versions


class SourceForgeLibraryProvider(TarballLibraryProvider):

    @classmethod
    def is_type(cls, origin=None):
        if origin is None:
            return False

        if 'sourceforge.net' in origin:
            return True

        return False

    def probe_remote_versions(self, source=None):
        if source is None:
            source = self.source

        return sourceforge_probe_remote_versions(source)

    def version_source_url(self, varname=None):
        return self.source
