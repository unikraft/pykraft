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

import click
from click.formatting import wrap_text
from click.termui import _ansi_colors
from click.termui import _ansi_reset_all

from .op import merge_dicts

CONTEXT_SETTINGS = dict(
    auto_envvar_prefix='UK',
    help_option_names=['-h', '--help'],
)

UNKNOWN_OPTIONS = merge_dicts(
    {'ignore_unknown_options': True},
    CONTEXT_SETTINGS
)


def _colorize(text, color=None):
    if not color:
        return text
    try:
        return '\033[%dm' % (_ansi_colors[color]) + text + _ansi_reset_all
    except KeyError:
        raise TypeError('Unknown color %r' % color)


class KraftHelpFormatter(click.HelpFormatter):
    def __init__(self, headers_color=None, options_color=None,
                 options_custom_colors=None, help_bash_color=None,
                 *args, **kwargs):
        self.headers_color = headers_color
        self.options_color = options_color
        self.options_custom_colors = options_custom_colors
        self.help_bash_color = help_bash_color
        super(KraftHelpFormatter, self).__init__(*args, **kwargs)

    def _pick_color(self, option_name):
        opt = option_name.split()[0]
        if (self.options_custom_colors and
                (opt in self.options_custom_colors.keys())):
            return self.options_custom_colors[opt]
        else:
            return self.options_color

    def write_usage(self, prog, args='', prefix='Usage: '):
        colorized_prefix = _colorize(prefix, color=self.headers_color)
        super(KraftHelpFormatter, self).write_usage(
            prog, args, prefix=colorized_prefix)

    def write_heading(self, heading):
        colorized_heading = _colorize(heading, color=self.headers_color)
        super(KraftHelpFormatter, self).write_heading(colorized_heading)

    def write_paragraph(self):
        """Writes a paragraph into the buffer."""
        if self.buffer:
            self.write('\n')

    def write_text(self, text):
        """Writes re-indented text into the buffer.  This rewraps and
        preserves paragraphs.
        """
        text_width = max(self.width - self.current_indent, 11)
        indent = ' ' * self.current_indent
        self.write(wrap_text(text, text_width,
                             initial_indent=indent,
                             subsequent_indent=indent,
                             preserve_paragraphs=True))
        self.write('\n')

    def write(self, text):
        if self.help_bash_color:
            text = re.sub(r'cmd\:\:(.*)', _colorize(r'\1', color=self.help_bash_color), text)
        if self.help_bash_color:
            text = re.sub(r'env\:\:(\w+)', _colorize(r'\1', color=self.help_bash_color), text)
        super(KraftHelpFormatter, self).write(text)

    def write_dl(self, rows, **kwargs):
        colorized_rows = [(_colorize(row[0], self._pick_color(row[0])), row[1])
                          for row in rows]
        super(KraftHelpFormatter, self).write_dl(colorized_rows, **kwargs)


class KraftHelpMixin(object):
    def __init__(self, help_headers_color=None, help_options_color=None,
                 help_options_custom_colors=None, help_bash_color=None,
                 *args, **kwargs):
        self.help_headers_color = help_headers_color
        self.help_options_color = help_options_color
        self.help_options_custom_colors = help_options_custom_colors
        self.help_bash_color = help_bash_color
        super(KraftHelpMixin, self).__init__(*args, **kwargs)

    def get_help(self, ctx):
        width = ctx.terminal_width or 120
        formatter = KraftHelpFormatter(
            width=width,
            max_width=ctx.max_content_width,
            headers_color=self.help_headers_color,
            options_color=self.help_options_color,
            options_custom_colors=self.help_options_custom_colors,
            help_bash_color=self.help_bash_color)
        self.format_help(ctx, formatter)
        return formatter.getvalue().rstrip('\n')


class KraftHelpGroup(KraftHelpMixin, click.Group):
    def __init__(self, *args, **kwargs):
        super(KraftHelpGroup, self).__init__(*args, **kwargs)
        self.help_headers_color = 'white'
        self.help_options_color = 'white'
        self.help_command_color = 'white'
        self.help_bash_color = 'white'

    def command(self, *args, **kwargs):
        kwargs.setdefault('cls', KraftHelpCommand)
        kwargs.setdefault('help_headers_color', self.help_headers_color)
        kwargs.setdefault('help_options_color', self.help_options_color)
        kwargs.setdefault('help_options_custom_colors',
                          self.help_options_custom_colors)
        kwargs.setdefault('help_bash_color', self.help_bash_color)
        return super(KraftHelpGroup, self).command(*args, **kwargs)

    def group(self, *args, **kwargs):
        kwargs.setdefault('cls', KraftHelpGroup)
        kwargs.setdefault('help_headers_color', self.help_headers_color)
        kwargs.setdefault('help_options_color', self.help_options_color)
        kwargs.setdefault('help_options_custom_colors',
                          self.help_options_custom_colors)
        kwargs.setdefault('help_bash_color', self.help_bash_color)
        return super(KraftHelpGroup, self).group(*args, **kwargs)

    def format_epilog(self, ctx, formatter):
        """Writes the epilog into the formatter if it exists."""
        if self.epilog:
            formatter.write(self.epilog)


class KraftHelpCommand(KraftHelpMixin, click.Command):
    def __init__(self, *args, **kwargs):
        super(KraftHelpCommand, self).__init__(*args, **kwargs)


class ClickOptionMutex(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop("not_required_if")
        assert self.not_required_if, "'not_required_if' parameter required"
        super(ClickOptionMutex, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current_opt = self.name in opts
        for mutex_opt in self.not_required_if:
            if mutex_opt in opts:
                if current_opt:
                    raise click.UsageError(
                        "Illegal usage: '" +
                        str(self.name) +
                        "' is mutually exclusive with " +
                        str(mutex_opt) + "."
                    )
                else:
                    self.prompt = None
        return super(ClickOptionMutex, self).handle_parse_result(ctx, opts, args)
