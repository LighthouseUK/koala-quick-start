"""
This configuration file loads environment's specific config settings for the application.
It takes precedence over the config located in the boilerplate package.
"""
from __future__ import absolute_import
import os
import codecs
from datetime import datetime
from ConfigParser import SafeConfigParser


__author__ = 'Matt Badger'


ENVIRONMENT_UNAWARE_SECTIONS = {'DEFAULT'}


class SettingsSection(object):
    pass


class CustomConfigParser(SafeConfigParser):
    def __init__(self, environment='Dev', *args, **kwargs):
        self.environment = environment

        SafeConfigParser.__init__(self, *args, **kwargs)
        pass

    def get(self, option, section='DEFAULT', raw=False, vars=None):
        section = self.prefix_section_environment(section)
        return SafeConfigParser.get(self, section, option, raw=False, vars=None)

    def getint(self, option, section='DEFAULT'):
        return int(self.get(option=option, section=section))

    def getfloat(self, option, section='DEFAULT'):
        return float(self.get(option=option, section=section))

    def getboolean(self, option, section='DEFAULT'):
        v = self.get(section=section, option=option)
        if v.lower() not in self._boolean_states:
            raise ValueError, 'Not a boolean: %s' % v
        return self._boolean_states[v.lower()]

    def getdate(self, option, section='Secrets', raw=False, vars=None):
        section = self.prefix_section_environment(section)
        value = SafeConfigParser.get(self, section, option, raw=False, vars=None)
        return datetime.strptime(value, '%Y-%m-%d')

    def getdatetime(self, option, section='Secrets', raw=False, vars=None):
        section = self.prefix_section_environment(section)
        value = SafeConfigParser.get(self, section, option, raw=False, vars=None)
        return datetime.strptime(value, '%Y-%m-%d %H%M%S')

    def getlist(self, option, section='DEFAULT', raw=False, vars=None):
        section = self.prefix_section_environment(section)
        setting = SafeConfigParser.get(self, section, option, raw=False, vars=None)
        return setting.split(',')

    def getdict_section(self, section):
        section = self.prefix_section_environment(section)
        options = self.items(section)
        return dict(options) if options else {}

    def getobject_section(self, section):
        section = self.prefix_section_environment(section)
        options = self.items(section)
        opt_dict = dict(options) if options else {}

        opt_object = SettingsSection()
        for k, v in opt_dict.iteritems():
            setattr(opt_object, k, v)

        return opt_object

    def items(self, section, raw=False, vars=None):
        section = self.prefix_section_environment(section)
        return SafeConfigParser.items(self, section, raw=raw, vars=vars)

    def options(self, section):
        section = self.prefix_section_environment(section)
        return SafeConfigParser.options(self, section)

    def prefix_section_environment(self, section):
        return self.environment + section if section not in ENVIRONMENT_UNAWARE_SECTIONS else section


# We can't just inherit from the above class as the config module uses old style classes :(
class SecretsParser(CustomConfigParser):
    def __init__(self, environment='Dev', *args, **kwargs):
        self.environment = environment

        SafeConfigParser.__init__(self, *args, **kwargs)
        pass

    def get(self, option, section='Secrets', raw=False, vars=None):
        section = self.prefix_section_environment(section)
        return SafeConfigParser.get(self, section, option, raw=False, vars=None)

    def getint(self, option, section='Secrets'):
        return int(self.get(option=option, section=section))

    def getfloat(self, option, section='Secrets'):
        return float(self.get(option=option, section=section))

    def getboolean(self, option, section='Secrets'):
        v = self.get(section=section, option=option)
        if v.lower() not in self._boolean_states:
            raise ValueError, 'Not a boolean: %s' % v
        return self._boolean_states[v.lower()]
        pass

    def getdate(self, option, section='Secrets', raw=False, vars=None):
        section = self.prefix_section_environment(section)
        value = SafeConfigParser.get(self, section, option, raw=False, vars=None)
        return datetime.strptime(value, '%Y-%m-%d')

    def getdatetime(self, option, section='Secrets', raw=False, vars=None):
        section = self.prefix_section_environment(section)
        value = SafeConfigParser.get(self, section, option, raw=False, vars=None)
        return datetime.strptime(value, '%Y-%m-%d %H%M%S')

    def getbyteliteral(self, option, section='Secrets', raw=False, vars=None):
        section = self.prefix_section_environment(section)
        value = SafeConfigParser.get(self, section, option, raw=False, vars=None)
        return bytes(value)

    def getlist(self, option, section='Secrets', raw=False, vars=None):
        section = self.prefix_section_environment(section)
        setting = SafeConfigParser.get(self, section, option, raw=False, vars=None)
        return setting.split(',')

    def getdict_section(self, section):
        section = self.prefix_section_environment(section)
        options = self.items(section)
        return dict(options) if options else {}

    def getobject_section(self, section):
        section = self.prefix_section_environment(section)
        options = self.items(section)
        opt_dict = dict(options) if options else {}

        opt_object = SettingsSection()
        for k, v in opt_dict.iteritems():
            setattr(opt_object, k, v)

        return opt_object

    def items(self, section, raw=False, vars=None):
        section = self.prefix_section_environment(section)
        return SafeConfigParser.items(self, section, raw=raw, vars=vars)

    def options(self, section):
        section = self.prefix_section_environment(section)
        return SafeConfigParser.options(self, section)

    def prefix_section_environment(self, section):
        return self.environment + section if section not in ENVIRONMENT_UNAWARE_SECTIONS else section


if "SERVER_SOFTWARE" in os.environ:
    if os.environ['SERVER_SOFTWARE'].startswith('Google'):
        platform = 'Production'
    elif os.environ['SERVER_NAME'] in ['localhost', '127.0.0.1']:
        platform = 'Dev'
    elif os.environ['SERVER_NAME'] == 'testbed.example.com':
        platform = 'Testing'
    else:
        raise ValueError("Environment undetected")
else:
    platform = 'Testing'

settings = CustomConfigParser(environment=platform, allow_no_value=True)
with codecs.open(os.path.join(os.path.dirname(__file__), 'app.ini'), 'r', encoding='utf-8') as f:
    settings.readfp(f)
settings.read([os.path.join(os.path.dirname(__file__), found_file) for found_file in os.listdir(os.path.dirname(__file__)) if found_file.endswith('.ini')])


# Dedicated config parser so that you can keep sensitive config out of your main config and also out of version control.
secrets = SecretsParser(environment=platform, allow_no_value=True)
with codecs.open(os.path.join(os.path.dirname(__file__), 'secrets.ini'), 'r', encoding='utf-8') as f:
    secrets.readfp(f)



