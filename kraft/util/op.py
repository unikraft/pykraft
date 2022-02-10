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

import contextlib
import os
import subprocess
import sys

from tqdm import tqdm
from tqdm.contrib import DummyTqdmFile

from kraft.logger import logger


def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def execute(cmd="", env={}, dry_run=False, use_logger=False):
    if type(cmd) is list:
        cmd = " ".join(cmd)

    logger.debug("Running: %s" % cmd)

    if not dry_run:
        popen = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            env=merge_dicts(os.environ, env)
        )

        for line in popen.stdout:
            line = line.strip().decode('utf-8')
            if use_logger:
                logger.info(line)
            else:
                print(line)

        popen.stdout.close()
        return_code = popen.wait()
        if return_code is not None and int(return_code) > 0:
            return return_code

    return 0


@contextlib.contextmanager
def std_out_err_redirect_tqdm():
    orig_out_err = sys.stdout, sys.stderr
    try:
        # sys.stdout = sys.stderr = DummyTqdmFile(orig_out_err[0])
        sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
        yield orig_out_err[0]

    # Relay exceptions
    except Exception as exc:
        raise exc

    # Always restore sys.stdout/err if necessary
    finally:
        sys.stdout, sys.stderr = orig_out_err


def make_progressbar(make=""):
    if make is None or len(make) == 0:
        return None

    make_n = make[:]
    make_n.append("-n")

    logger.debug("Calculating how many files to build...")
    logger.debug(" ".join(make_n))

    all_make_commands = subprocess.check_output(make_n)
    all_make_commands = all_make_commands.decode('utf-8').split('\n')
    actual_make_commands = []

    for i, command in enumerate(all_make_commands):
        command = command.strip()
        if command.startswith('make') \
                or command == "" \
                or command == ":" \
                or "fixdep" in command:
            pass

        else:
            actual_make_commands.append(command)

    with std_out_err_redirect_tqdm() as orig_stdout:
        logger.debug("Starting build...")
        logger.debug(" ".join(make))

        popen = subprocess.Popen(
            make,
            stdout=subprocess.PIPE,
            env=os.environ
        )

        with tqdm(
            total=len(actual_make_commands),
            file=orig_stdout,
            unit="file",
            leave=False,
            bar_format="{desc:<3}{percentage:3.0f}% {bar} {n_fmt}/{total_fmt} [{rate_fmt}{postfix}]",
            dynamic_ncols=True) as t:  # noqa: E125

            for line in popen.stdout:
                t.update()
                line = line.strip().decode('utf-8')
                if line.startswith("make: Leaving directory") is False and \
                        line.startswith("make: Entering directory") is False:
                    print(line)

            t.close()

        popen.stdout.close()
        return popen.wait()

    return 0
