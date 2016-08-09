# -*- coding: utf-8 -*-
"""
    Koala Quick Start Example API
    ~~~~~~~~~~~~~~~~~~


    :copyright: (c) 2015 Lighthouse
    :license: LGPL
"""
import config
import koalacore
from blinker import signal
# Import the packages that will make up this API
from koalausers import Users
from koalacompanies import Companies
from koalaverify import Verification
from koalasendgrid import send_email
from koalamail import EmailRenderer

__author__ = 'Matt Badger'

# We give admin the same permissions that would normally be applied at the company level so that they can 'impersonate'
# any company in the system. Generally not actually needed because we do a global check for company permission in the
# myguild endpoint before the request is processed.
GLOBAL_ACL = {
    'admin': {'admin_users'},
    'user': {}
}

RBAC = koalacore.RBAC
RBAC.configure(global_acl=GLOBAL_ACL)

GLOBAL_RENDERER_VARS = {
    'app_info': {
        'app_name': config.settings.get('app_name'),
        'title': config.settings.get('title'),
        'url': config.settings.get('url'),
        'copyright': config.settings.get('copyright'),
        'support_email': config.settings.get('support_email'),
        'support_url': config.settings.get('support_url'),
    },
}

JINJA2_ENGINE_CONFIG = {
    'environment_args': {'extensions': config.settings.getlist('jinja2_extensions'),
                         'autoescape': config.settings.getboolean('jinja2_env_autoescape')},
    'theme_base_template_path': config.settings.getlist('email_template_base_path'),
    'theme_compiled_path': config.settings.get('email_template_compiled_path'),
    'enable_i18n': config.settings.getboolean('jinja2_enable_i18n'),
}

RENDERER_CONFIG = {
    'jinja2_engine_config': JINJA2_ENGINE_CONFIG,
    'global_renderer_vars': GLOBAL_RENDERER_VARS,
}


EmailRenderer.configure(configuration=RENDERER_CONFIG)


class Notifications(object):
    @classmethod
    def send_email(cls, **kwargs):
        """
        Invokes the email sending package, which wraps the sendgrid library.

        :param kwargs - see the koalasendgrid library
        :raises SendGridClientError
        :raises SendGridServerError
        """
        return send_email(**kwargs)


# This is an example of how you could setup deferred tasks without having to setup up a dedicated receiver function
# signal('insert_user.hook').connect(lambda *args, **kwargs: deferred.defer(_update_user_search_index, entity_id=kwargs['entity_id'], _queue='backend'), sender=Users)