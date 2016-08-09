# -*- coding: utf-8 -*-
import webapp2
import koalacore
import config
import logging
import appapi
from jerboa.statusmanager import StatusManager, parse_request_status_code
from jerboa.routes import Component
from jerboa.forms import LoginForm, ForgottenPasswordForm, ResetPasswordForm
from blinker import signal
from jerboa.extra import StandardFormHandler, CallbackFailed, UIFailed, FormDuplicateValue
from jerboa.exceptions import UserLoggedInException
from google.appengine.api import users

__author__ = 'Matt Badger'

component = Component(name='authentication', title='Authentication')

INVALID_CREDENTIALS_STATUS = StatusManager.add_status(message=u'Sorry, the login details you supplied are invalid.',
                                                      status_type=u'alert')

INVALID_AUTH_ID_STATUS = StatusManager.add_status(message=u'Sorry, the username or email address you supplied is not '
                                                          u'in our system.',
                                                  status_type=u'alert')

INVALID_USERNAME_STATUS = StatusManager.add_status(message=u'Sorry, the username you supplied is not in our system.',
                                                   status_type=u'alert')

INVALID_PASSWORD_STATUS = StatusManager.add_status(message=u'Sorry, the password you supplied is incorrect.',
                                                   status_type=u'alert')

LOGOUT_SUCCESS_STATUS = StatusManager.add_status(message=u'Successfully logged out.', status_type=u'success')

FORGOTTEN_PASSWORD_EMAIL_SENT_STATUS = StatusManager.add_status(message=u'Successfully sent forgotten password email. '
                                                                        u'Please check your inbox.',
                                                                status_type=u'success')

INVALID_RESET_TOKEN_STATUS = StatusManager.add_status(message=u'Invalid reset password token. Please use the '
                                                              u'"forgotten_password?" link to try again.',
                                                      status_type=u'alert')

EXPIRED_RESET_TOKEN_STATUS = StatusManager.add_status(message=u'Sorry, that reset password token has expired. Please '
                                                              u'use the "Forgotten your Password?" link to try again.',
                                                      status_type=u'alert')


def login_callback(self, request, response, form):
    verified, result = appapi.Users.get_by_auth_details_and_verify(auth_id=form.auth_id.data,
                                                                      password=form.password.data)

    if not verified:
        if result == u'Invalid username or email address':
            self.set_redirect_url(request=request, response=response, handler=self.ui_name,
                                  status_code=INVALID_USERNAME_STATUS)
            raise CallbackFailed(u'Invalid username or email address')
        elif result == u'Password does not match':
            self.set_redirect_url(request=request, response=response, handler=self.ui_name, auth_id=form.auth_id.data,
                                  status_code=INVALID_PASSWORD_STATUS)
            raise CallbackFailed(u'Password does not match')
        else:
            self.set_redirect_url(request=request, response=response, handler=self.ui_name,
                                  status_code=INVALID_CREDENTIALS_STATUS)
            raise CallbackFailed(u'Invalid credentials')
    else:
        request.environ['beaker.session']['user_uid'] = result.uid


login_handlers = StandardFormHandler(
    component=component,
    form=LoginForm,
    validation_trigger_codes=[INVALID_CREDENTIALS_STATUS, INVALID_USERNAME_STATUS, INVALID_PASSWORD_STATUS],
    handler_name=u'login',
    success_function=login_callback,
    suppress_success_status=True,
    handler_map={u'login.success': u'default', u'default': u'default'}
)


def set_registration_url(sender, request, response):
    response.raw.register_url = sender.build_url_with_continue_support(request=request,
                                                                       uri_for='component.user.register.ui')


signal('login.ui.hook').connect(set_registration_url, sender=login_handlers)


# TODO: these kinda need CSRF protection to prevent someone else logging them out
def logout(request, response):
    request.environ['beaker.session'].delete()
    parse_request_status_code(request=request, response=response)


def logout_callback(request, response):
    request.environ['beaker.session'].delete()
    parse_request_status_code(request=request, response=response)


def forgotten_password_callback(self, request, response, form):
    user = appapi.Users.get_by_auth_id(auth_id=form.auth_id.data)
    reset_route_path = 'component.authentication.reset.ui'

    if user:
        token = appapi.Verification.generate(token_uid=user.uid,
                                                redirect_uri=reset_route_path)

        verification_url = webapp2.uri_for(reset_route_path, token=token, _full=True)
        email_template_vars = {
            'title': u'Password Reset Request',
            'copy': u'We have received a request to reset your user account password. If you did not make this request then please ignore this email.<br /><br /> Please click the following link to reset your password: <a href="{}">{}</a><br /><br />Please note: this link can only be used once. If you make a mistake you will need to request another by clicking on "Forgotten your Password?" again. The link will expire in 12 hours.'.format(verification_url, verification_url),
        }

        send_email_kwargs = {
            'to_address': user.email_address,
            'subject': u'Password Reset Request',
            'to_name': u'{0} {1}'.format(user.first_name, user.last_name),
            'body': appapi.EmailRenderer.render(
                template_path=config.settings.get('user_notification_email_template'),
                template_vars=email_template_vars)
        }

        send_response = appapi.Notifications.send_email(**send_email_kwargs)
        if send_response.status_code in [200, 201, 202]:
            logging.debug(u'User notification email successfully sent')
        else:
            logging.error(u'User notification email failed to send: {}'.format(send_response.body))

        self.set_redirect_url(request=request, response=response, handler=u'forgotten.success',
                              status_code=FORGOTTEN_PASSWORD_EMAIL_SENT_STATUS)
    else:
        self.set_redirect_url(request=request, response=response, handler=self.ui_name,
                              status_code=INVALID_AUTH_ID_STATUS)
        raise CallbackFailed(u'Invalid credentials')


forgot_password_handlers = StandardFormHandler(
    component=component,
    form=ForgottenPasswordForm,
    handler_name=u'forgotten',
    success_function=forgotten_password_callback,
    suppress_success_status=True,
    handler_map={u'forgotten.success': u'login.ui'},
)


def reset_password_callback(self, request, response, form):
    valid, token = appapi.Verification.verify(token=form.token.data,
                                                 redirect_uri='component.authentication.reset.ui')

    if not valid:
        self.set_redirect_url(request=request, response=response, handler=u'login.ui',
                              status_code=INVALID_RESET_TOKEN_STATUS)
        raise CallbackFailed(u'Invalid reset password token')

    user = appapi.Users.get(resource_uid=token.token_uid)
    user.change_password(raw_password=form.password.data)
    appapi.Users.update(resource_object=user)


reset_password_handlers = StandardFormHandler(
    component=component,
    form=ResetPasswordForm,
    handler_name=u'reset',
    success_function=reset_password_callback,
    success_message=u'Successfully reset password. Please log in below.',
    force_ui_get_data=True,
    handler_map={u'login.ui': u'login.ui', u'reset.success': u'login.ui'},
)


def check_token_present(sender, request, response):
    if not request.params.get(u'token'):
        sender.set_redirect_url(request=request, response=response, handler=u'login.ui',
                                status_code=INVALID_RESET_TOKEN_STATUS)
        raise UIFailed(u'Missing reset token')


signal('reset.ui.hook').connect(check_token_present, sender=reset_password_handlers)


def sysadmin(request, response):
    callback = webapp2.uri_for('component.authentication.sysadmin.action')
    redirect_url = users.create_login_url(dest_url=callback)
    webapp2.redirect(uri=redirect_url, request=request, response=response)
    return response


def sysadmin_callback(request, response):
    logged_in_user = users.get_current_user()

    if not logged_in_user or not users.is_current_user_admin():
        redirect_url = webapp2.uri_for('component.authentication.login.ui')
        webapp2.redirect(uri=redirect_url, request=request, response=response)
        return response

    registered_user = appapi.Users.get_by_auth_id(auth_id=logged_in_user.user_id())

    if registered_user:
        # Sync user with the Google UserAPI
        modified = False
        if registered_user.email_address != logged_in_user.email():
            registered_user.email_address = logged_in_user.email()
            modified = True

        if 'admin' not in registered_user.permissions.roles:
            registered_user.permissions.add_role('admin')
            modified = True
        if 'sysadmin' not in registered_user.permissions.roles:
            registered_user.permissions.add_role('sysadmin')
            modified = True

        if modified:
            appapi.Users.update(resource_object=registered_user)
        registered_user_uid = registered_user.uid
    else:
        random_password = koalacore.generate_random_string(20)

        user = appapi.Users.new(username=logged_in_user.user_id(),
                                   email_address=logged_in_user.email(),
                                   email_address_verified=True,
                                   first_name=u'Sys',
                                   raw_password=random_password,
                                   last_name=u'Admin',
                                   language_preference=u'en',
                                   roles={'user', 'admin', 'sysadmin'})

        try:
            user_uid = appapi.Users.insert(resource_object=user)
        except koalacore.UniqueValueRequired:
            redirect_url = webapp2.uri_for('component.authentication.login.ui', status_code='16')
            webapp2.redirect(uri=redirect_url, request=request, response=response)
            return response
        registered_user_uid = user_uid

    request.environ['beaker.session']['user_uid'] = registered_user_uid

    redirect_url = webapp2.uri_for('default')
    webapp2.redirect(uri=redirect_url, request=request, response=response)
    return response


# Prevent logged in users from accessing these pages to improve the UX
def block_if_user(sender, request, response):
    if 'user_uid' in request.environ['beaker.session']:
        raise UserLoggedInException


signal('login.ui.hook').connect(block_if_user, sender=login_handlers)
signal('forgotten.ui.hook').connect(block_if_user, sender=forgot_password_handlers)
signal('pre_forgotten.action.hook').connect(block_if_user, sender=forgot_password_handlers)
signal('reset.ui.hook').connect(block_if_user, sender=reset_password_handlers)
signal('pre_reset.action.hook').connect(block_if_user, sender=reset_password_handlers)

component.add_route(route_type='rendered', route_name='sysadmin', route_title='System Admin Login', handler=sysadmin,
                    auto_url_prefix=False, login_required=False)
component.add_route(route_type='action', route_name='sysadmin', handler=sysadmin_callback, login_required=False)

component.add_route(route_type='rendered', route_name='login', route_title='Login', handler=login_handlers.ui_handler,
                    auto_url_prefix=False, login_required=False)

component.add_route(route_type='action', route_name='login', handler=login_handlers.callback_handler,
                    login_required=False)

component.add_route(route_type='rendered', route_name='logout', handler=logout, auto_url_prefix=False)
component.add_route(route_type='action', route_name='logout', handler=logout_callback, )

component.add_route(route_type='rendered', route_name='forgotten', route_title='Reset Forgotten Password',
                    handler=forgot_password_handlers.ui_handler, auto_url_prefix=False, login_required=False)

component.add_route(route_type='action', route_name='forgotten',
                    handler=forgot_password_handlers.callback_handler, login_required=False)

component.add_route(route_type='rendered', route_name='reset', route_title='Reset Forgotten Password',
                    handler=reset_password_handlers.ui_handler, auto_url_prefix=False, login_required=False)

component.add_route(route_type='action', route_name='reset', handler=reset_password_handlers.callback_handler,
                    login_required=False)