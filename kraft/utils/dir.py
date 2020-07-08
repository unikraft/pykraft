# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#          Gaulthier Gain <gaulthier.gain@uliege.be>
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

import os
import shutil
from shutil import copyfile
from shutil import SameFileError
from pathlib import Path

from kraft.logger import logger

def existing_path(path):
    """Return a boolean of whether the provided `path` exists."""
    return os.path.exists(path)  

def get_home_dir():
    """Return a string which represents the current home directory."""
    return str(Path.home())

def is_dir_empty(path=None):
    """Return a boolean of whether the provided directory `dir` is empty."""
    return os.path.isdir(path) is False or \
        len([f for f in os.listdir(path) if not f.startswith('.')]) == 0


def recursively_copy(src, dest, overwrite=False, ignore=[]):
    if os.path.basename(src) in ignore:
        pass
    elif os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)

        files = os.listdir(src)

        for f in files:
            recursively_copy(
                os.path.join(src, f),
                os.path.join(dest, f),
                overwrite,
                ignore
            )
    elif (os.path.exists(dest) and overwrite) or os.path.exists(dest) is False:
        try:
            copyfile(src, dest)
        except SameFileError:
            pass


def delete_resource(resource):
    if os.path.isfile(resource):
        logger.debug("Removing file: %s" % resource)
        os.remove(resource)

    elif os.path.isdir(resource):
        logger.debug("Removing directory: %s" % resource)
        shutil.rmtree(resource)
