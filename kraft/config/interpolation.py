from __future__ import absolute_import
from __future__ import unicode_literals

import re
from string import Template

from kraft.errors import InvalidInterpolation

class Interpolator(object):

    def __init__(self, templater, mapping):
        self.templater = templater
        self.mapping = mapping

    def interpolate(self, string):
        try:
            return self.templater(string).substitute(self.mapping)
        except ValueError:
            raise InvalidInterpolation(string)

class TemplateWithDefaults(Template):
    pattern = r"""
        %(delim)s(?:
            (?P<escaped>%(delim)s) |
            (?P<named>%(id)s)      |
            {(?P<braced>%(bid)s)}  |
            (?P<invalid>)
        )
        """ % {
        'delim': re.escape('$'),
        'id': r'[_a-z][_a-z0-9]*',
        'bid': r'[_a-z][_a-z0-9]*(?:(?P<sep>:?[-?])[^}]*)?',
    }

    @staticmethod
    def process_braced_group(braced, sep, mapping):
        if ':-' == sep:
            var, _, default = braced.partition(':-')
            return mapping.get(var) or default
        elif '-' == sep:
            var, _, default = braced.partition('-')
            return mapping.get(var, default)

        elif ':?' == sep:
            var, _, err = braced.partition(':?')
            result = mapping.get(var)
            if not result:
                raise UnsetRequiredSubstitution(err)
            return result
        elif '?' == sep:
            var, _, err = braced.partition('?')
            if var in mapping:
                return mapping.get(var)
            raise UnsetRequiredSubstitution(err)

    # Modified from python2.7/string.py
    def substitute(self, mapping):
        # Helper function for .sub()

        def convert(mo):
            named = mo.group('named') or mo.group('braced')
            braced = mo.group('braced')
            if braced is not None:
                sep = mo.group('sep')
                if sep:
                    return self.process_braced_group(braced, sep, mapping)

            if named is not None:
                val = mapping[named]
                if isinstance(val, six.binary_type):
                    val = val.decode('utf-8')
                return '%s' % (val,)
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                self._invalid(mo)
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)



def interpolate_environment_variables(version, config, section, environment):
    
    interpolator = Interpolator(TemplateWithDefaults, environment)

    def process_item(name, config_dict):
        return dict(
            (key, interpolate_value(name, key, val, section, interpolator))
            for key, val in (config_dict or {}).items()
        )

    return dict(
        (name, process_item(name, config_dict or {}))
        for name, config_dict in config.items()
    )
