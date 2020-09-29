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
import yaml

from kraft.util import delete_resource

from kraft.const import TEMPLATE_CONFIG
from kraft.const import TEMPLATE_MANIFEST


def get_templates_path(templatedir=None):
    if templatedir is None:
        raise ValueError("expected templatedir")
    return os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      templatedir
    )

def get_template_config(templatedir=None):
    if templatedir is None:
        raise ValueError("expected templatedir")

    return os.path.join(
        get_templates_path(templatedir),
        TEMPLATE_CONFIG
    )

def delete_template_resources_of_disabled_features(templatedir=None):
    if templatedir is None:
        return

    template_manifest = os.path.join(templatedir, TEMPLATE_MANIFEST)

    if os.path.exists(template_manifest) is False:
        return

    with open(template_manifest) as manifest_file:
        manifest = yaml.load(manifest_file, Loader=yaml.FullLoader)

        for feature in manifest['features']:
            if not feature['enabled']:
                for resource in feature['resources']:
                    delete_resource(os.path.join(templatedir, resource))

    delete_resource(template_manifest)
