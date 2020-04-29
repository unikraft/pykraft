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

PROVIDER_STATUS_AVAILABLE = "available"
PROVIDER_STATUS_OUTOFDATE = "outofdate"
PROVIDER_STATUS_EMPTY = "empty"

class Provider(object):
    _source = None

    def __init__(self, source=None):
        self.source = source
    
    @classmethod
    def is_type(self):
        pass
    
    def probe_remote_versions(self, source=None):
        return []
    
    def version_source_archive(self, varname=None):
        return self.source

    @property
    def source(self):
        return self._source
    
    @source.setter
    def source(self, source=None):
        self._source = source

    # def __init__(self, source):
    #     self.source = source
    #     self.cacheable = False

    #     # self.localdir = localdir
    #     # self.cachable = not (config.get("cachable", "") == False)
    #     # self.patches = []



    # @kraft_context
    # def clean_cache(self, ctx):
    #     pass
    #     # if os.path.exists(self.localdir):
    #     #     shutil.rmtree(self.localdir)

    # def fetch(self):
    #     status = self.status()

    #     if status == PROVIDER_STATUS_EMPTY:
    #         self._checkout(self.localdir)
    #         _fetched = True

    #     elif status == PROVIDER_STATUS_OUTOFDATE:
    #         self.clean_cache()
    #         self._checkout(self.localdir)
    #         _fetched = True

    #     elif status == PROVIDER_STATUS_AVAILABLE:
    #         _fetched = False

    #     else:
    #         raise RuntimeError(
    #             "Provider status is: '" + status + "'. This shouldn't happen"
    #         )
        
    #     # if _fetched:
    #     #     self._patch()

    # # def _patch(self):
    # #     for f in self.patches:
    # #         patch_file = os.path.abspath(os.path.join(self.core_root, f))
    # #         if os.path.isfile(patch_file):
    # #             logger.debug(
    # #                 "  applying patch file: "
    # #                 + patch_file
    # #                 + "\n"
    # #                 + "                   to: "
    # #                 + os.path.join(self.localdir)
    # #             )
    # #             try:
    # #                 Launcher("git", ["apply", patch_file], self.localdir).run()
    # #             except OSError:
    # #                 raise RuntimeError("Failed to call 'git' for patching core")

    # def status(self):
    #     if not self.cachable:
    #         return PROVIDER_STATUS_OUTOFDATE
    #     if not os.path.isdir(self.localdir):
    #         return PROVIDER_STATUS_EMPTY
    #     else:
    #         return PROVIDER_STATUS_AVAILABLE


