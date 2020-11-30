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

import threading

import six
from fcache.cache import FileCache

from kraft import __program__
from kraft.logger import logger
from kraft.manifest import Manifest


class Cache(object):
    _cache = {}
    _cachedir = None
    _cache_lock = None
    @property
    def cache_lock(self): return self._cache_lock

    def __init__(self, environment):
        """
        Initializes the cache so that kraft does not have to constantly
        retrieve informational lists about unikraft, its available
        architectures, platforms, libraries and supported applications.
        """

        self._cachedir = environment.get('UK_CACHEDIR')

        # Initiaize a cache instance
        self._cache = FileCache(
            app_cache_dir=self._cachedir,
            appname=__program__,
            flag='cs'
        )

        self._cache_lock = threading.Lock()

    @property
    def cache(self):
        ret = None
        with self._cache_lock:
            ret = self._cache
        return ret

    def get(self, origin=None):
        ret = None
        if isinstance(origin, six.string_types) and origin in self._cache:
            logger.debug("Retrieving %s from cache..." % origin)
            with self._cache_lock:
                ret = self._cache[origin]

        return ret

    def find_item_by_name(self, type=None, name=None):
        for origin in self._cache:
            for item in self._cache[origin].items():
                if ((type is not None and item[1].type.shortname == type)
                        or type is None) and item[1].name == name:
                    return item[1]

        return None

    def all(self):
        return self.cache

    def save(self, origin, manifest):
        if not isinstance(origin, six.string_types):
            raise TypeError("origin is not string")
        if not isinstance(manifest, Manifest):
            raise TypeError("Invalid manifest")

        with self._cache_lock:
            logger.debug("Saving %s into cache..." % manifest)
            self._cache[origin] = manifest

    def sync(self):
        logger.debug("Synchronizing cache with filesystem...")

        with self._cache_lock:
            self._cache.sync()

    def purge(self):
        logger.debug("Purging cache...")

        with self._cache_lock:
            self._cache.clear()

    def is_stale(self):
        """
        Determine if the list of remote repositories is stale.  Return a boolean
        value if at least one repository is marked as stale.
        """

        logger.debug("Checking cache for staleness...")
        return True if len(self.all()) == 0 else False
