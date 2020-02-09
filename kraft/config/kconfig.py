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

from kraft.errors import KconfigFileNotFound

def split_kconfig(kconfig):
    if isinstance(kconfig, six.binary_type):
        kconfig = kconfig.decode('utf-8', 'replace')
    key = value = None
    if '=' in kconfig:
        key, value = kconfig.split('=', 1)
    else:
        key = kconfig
    if re.search(r'\s', key):
        raise ConfigurationError(
            "Kconfig variable name '%s' may not contain whitespace." % key
        )
    return key, value


def kconfig_from_file(filename):
    """
    Read in a line delimited file of Kconfig variables.
    """
    if not os.path.exists(filename):
        raise KconfigFileNotFound("Couldn't find Kconfig file: %s" % filename)
    elif not os.path.isfile(filename):
        raise KconfigFileNotFound("%s is not a file." % filename)

    return dotenv.dotenv_values(dotenv_path=filename, encoding='utf-8-sig')

class Kconfig(dict):
    def __init__(self, *args, **kwargs):
        super(Kconfig, self).__init__(*args, **kwargs)
        self.missing_keys = []
        self.silent = False

    @classmethod
    def from_file(cls, base_dir, kconfig_file=None):
        result = cls()
        if base_dir is None:
            return result
        if kconfig_file:
            kconfig_file_path = os.path.join(base_dir, kconfig_file)
        else:
            kconfig_file_path = os.path.join(base_dir, '.kconfig')
        try:
            return cls(kconfig_vars_from_file(kconfig_file_path))
        except EnvFileNotFound:
            pass
        return result

    def __getitem__(self, key):
        try:
            return super(Kconfig, self).__getitem__(key)
        except KeyError:
            if not self.silent and key not in self.missing_keys:
                log.warning(
                    "The %s variable is not set. Defaulting to a blank string."
                    % key
                )
                self.missing_keys.append(key)

            return ""

    def __contains__(self, key):
        result = super(Kconfig, self).__contains__(key)
        return result

    def get(self, key, *args, **kwargs):
        return super(Kconfig, self).get(key, *args, **kwargs)

    def get_boolean(self, key):
        # Convert a value to a boolean using "common sense" rules.
        # Unset, empty, "0" and "false" (i-case) yield False.
        # All other values yield True.
        value = self.get(key)
        if not value:
            return False
        if value.lower() in ['0', 'false']:
            return False
        return True



    def indent_print(s, indent):
        print(indent*" " + s)


    def traverse_config(node, indent):
        while node:
            if isinstance(node.item, Symbol):
                indent_print("config " + node.item.name, indent)

            elif isinstance(node.item, Choice):
                indent_print("choice", indent)

            elif node.item == MENU:
                indent_print('menu "{}"'.format(node.prompt[0]), indent)

            elif node.item == COMMENT:
                indent_print('comment "{}"'.format(node.prompt[0]), indent)

            if node.list:
                self.traverse_config(node.list, indent + 2)

            node = node.next
