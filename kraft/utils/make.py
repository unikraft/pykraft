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

import re
import subprocess


def make_list_vars(Makefile=None, origin=None):
    """
    Generate the (key, value) dict of all variables defined in make process.

    Args:
        Makefile:  The location of the Makefile to expand.
        origin:  The means of selecting where the variable is derived from.
            Choose from: 'automatic', 'environment', 'default', 'override',
            'makefile'.  Setting to None returns all origins.

    Returns:
        A dict mapping keys to the corresponding variable.
    """

    p = subprocess.getoutput("make -pnB -f %s" % Makefile)

    M = {}
    re_var = re.compile(r"^#\s*Variables\b")  # start of variable segment
    re_varend = re.compile(r"^#\s*variable")  # end of variables
    state = None  # state of parser
    mname = None

    for line in p.splitlines():
        if state is None and re_var.search(line):
            state = 'var'

        elif state == 'var':
            line = line.strip()

            if re_varend.search(line):  # last line of variable block
                state = 'end'
                break

            if line.startswith("#"):  # type of variable
                q = line.split()
                mname = q[1]

            elif mname is not None:
                if origin is not None and mname not in origin:
                    continue

                if mname not in M:
                    M[mname] = {}

                q = line.split(maxsplit=2)  # key =|:= value

                if len(q) == 2:
                    M[mname][q[0]] = ''
                else:
                    M[mname][q[0]] = q[2]

                mname = None

    return M
