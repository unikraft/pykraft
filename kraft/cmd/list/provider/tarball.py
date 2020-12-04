# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Laboratories Europe GmbH., NEC Corporation.
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
# flake8: noqa
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import threading
import time
import urllib.request
import uuid
from email.utils import parsedate_tz
from math import ceil
from os.path import join
from time import mktime

import click
import requests
from atpbar import find_reporter

from .provider import ListProvider
from kraft.const import UNIKRAFT_CACHEDIR
from kraft.logger import logger


class FileDownloader(object):
    CHUNK_SIZE = 1024

    def __init__(self, url, dest=None, label=None):
        self._url = url
        self._destination = dest
        self._progressbar = None
        self._request = None

        # make connection
        self._request = requests.get(url, stream=True)
        print(self._request.headers)
        if self._request.status_code != 200:
            pass
            # raise FDUnrecognizedStatusCode(self._request.status_code, url)

    def set_destination(self, destination):
        self._destination = destination

    def get_filepath(self):
        return self._destination

    def get_lmtime(self):
        if 'last-modified' in self._request.headers:
            return self._request.headers['last-modified']

    def get_size(self):
        return int(self._request.headers['Content-Length'])

    def start(self):
        itercontent = self._request.iter_content(chunk_size=self.CHUNK_SIZE)
        f = open(self._destination, "wb")
        chunks = int(ceil(self.get_size() / float(self.CHUNK_SIZE)))

        with click.progressbar(
                length=chunks,
                label="Downloading",
                show_pos=True,
                width=0,
            ) as pb:
            time.sleep(0.5)
            for _ in pb:
                f.write(next(itercontent))

        f.close()
        self._request.close()

    def __del__(self):
        if self._request:
            self._request.close()


class TarballProgressBar(object):
    def __init__(self, label=None):
        self.taskid = uuid.uuid4()
        self.reporter = find_reporter()
        self.pid = os.getpid()
        self.label = label
        self.total = 0

    def update_to(self, b=1, bsize=1, tsize=0):
        if tsize is not None and tsize > 0:
            self.total = tsize / 1024
        elif (b * bsize) > self.total:
            pass
        else:
            self.total += (b * bsize) / 1024

        self.reporter.report(dict(
            taskid=self.taskid,
            name=self.label,
            done=int((b * bsize) / 1024),
            total=int(self.total),
            pid=self.pid,
            # pid=threading.current_thread().ident,
            in_main_thread=True
            # in_main_thread=False
        ))


class TarballListProvider(ListProvider):
    @click.pass_context
    def download(ctx, self, manifest=None, localdir=None, version=None,
            override_existing=False):

        if version.tarball is None:
            logger.warn("Cannot download tarball, not in manifest")
            return

        remote = manifest.get_version(version.version).tarball

        if remote.endswith(".tar.gz"):
            ext = ".tar.gz"
        else:
            _, ext = os.path.splitext(remote)

        local = os.path.join(
            ctx.obj.env.get('UK_CACHEDIR', os.path.join(
                ctx.obj.workdir,
                UNIKRAFT_CACHEDIR)
            ),
            "%s-%s%s" % (manifest.name, version.version, ext)
        )

        logger.debug("Downloading %s..." % remote)

        t = TarballProgressBar(label="%s/%s@%s"
            % (manifest.type.shortname, manifest.name, version.version)
        )
        urllib.request.urlretrieve(
            remote,
            filename=local,
            reporthook=t.update_to,
            data=None
        )

        # dl = FileDownloader(remote, local)
        # dl.start()
