# -*- coding: utf-8 -*-
import webapp2
import wtforms
import config
import logging
from webapp2_extras.i18n import _lazy as _
from jerboa.routes import Component
from jerboa.forms import BaseModelForm, NameMixin, UsernameMixin, EmailAddressMixin, ConfirmPasswordMixin, \
    LanguagePreferenceMixin, RecaptchaMixin, BaseSearchForm, GAEFilterOptions, FormField, DEFAULT_NONE_VALUE, \
    LanguageCodeValidationWithDefaultSupport, GAESearchCursorMixin, GAESortOptions
from jerboa.utils import STATIC_LANGUAGE_CODES_TUPLE
from jerboa.extra import CrudHandler, SearchHandler, FormDuplicateValue
from jerboa.statusmanager import StatusManager, parse_request_status_code
from jerboa.exceptions import UserLoggedInException
from blinker import signal
import appapi
import koalacore

__author__ = 'Matt Badger'


component = Component(name=u'user', title=u'User')


REQUEST_CONFIG_KEYS = [u'csrf_config', u'recaptcha_config']

CRUD_FILTER_PARAMS = [u'password', u'c_password']

CRUD_HANDLER_MAP = {u'crud_default': u'profile.ui',
                    u'create.ui': u'register.ui',
                    u'read.ui': u'profile.ui',
                    u'create_success': u'profile.ui',
                    u'update_success': u'profile.ui'}

PROPERTY_MAP = {
    u'username': _(u'Username'),
    u'first_name': _(u'First Name'),
    u'last_name': _(u'Last Name'),
    u'email_address': _(u'Primary Email'),
    u'recovery_email_address': _(u'Recovery Email'),
    u'language_preference': _(u'Language'),
    u'created': _(u'Registered'),
    u'updated': _(u'Updated'),
}

PROPERTY_VIEW_LIST = [
    u'username',
    u'first_name',
    u'last_name',
    u'email_address',
    u'recovery_email_address',
    u'language_preference',
    u'created',
    u'updated',
]

DISABLED_CREATE_PROPERTIES = [
    u'uid',
    u'csrf',
]

DISABLED_UPDATE_PROPERTIES = [
    u'username',
    u'recaptcha2',
    u'g-recaptcha-response',
    u'password',
    u'c_password',
]

SORT_OPTIONS = (
    (u'NONE', _(u'None')),
    (u'username', _(u'Username')),
    (u'first_name', _(u'First Name')),
    (u'last_name', _(u'Last Name')),
    (u'email_address', _(u'Primary Email')),
    (u'recovery_email_address', _(u'Recovery Email')),
    (u'language_preference', _(u'Language')),
    (u'created', _(u'Registered')),
    (u'updated', _(u'Updated')),
)

LANG_LIST = [(DEFAULT_NONE_VALUE, u'--')]
LANG_LIST.extend(list(STATIC_LANGUAGE_CODES_TUPLE))
LANG_TUPLE = tuple(LANG_LIST)


class UserForm(BaseModelForm, NameMixin, UsernameMixin, EmailAddressMixin, ConfirmPasswordMixin, LanguagePreferenceMixin, RecaptchaMixin):
    pass


class UserSortOptions(GAESortOptions):
    sort_by = wtforms.fields.SelectField(_(u'Sort By'), [], choices=SORT_OPTIONS, default=DEFAULT_NONE_VALUE)


class UserFilterOptions(GAEFilterOptions):
    language_preference = wtforms.fields.SelectField(_(u'Preferred Language'), [
        LanguageCodeValidationWithDefaultSupport,
    ], choices=LANG_TUPLE, default=DEFAULT_NONE_VALUE)


class UserSearchForm(BaseSearchForm, GAESearchCursorMixin):
    sort_options = FormField(UserSortOptions)
    filter_options = FormField(UserFilterOptions)


class UserCRUDHandlers(CrudHandler):
    def _load_model(self, uid):
        return appapi.Users.get(resource_uid=uid)

    def _do_create(self, request, response, form):
        user = appapi.Users.new(username=form.username.data,
                                   email_address=form.email_address.data,
                                   first_name=form.first_name.data,
                                   raw_password=form.password.data,
                                   last_name=form.last_name.data,
                                   language_preference=form.language_preference.data)
        try:
            user_uid = appapi.Users.insert(resource_object=user)
        except koalacore.UniqueValueRequired, e:
            raise FormDuplicateValue(duplicates=e.errors)

        # TODO: convert this to use the built in uri generators?

        token = appapi.Verification.generate(token_uid=user_uid, redirect_uri='component.user.verify_email.action')
        verification_url = webapp2.uri_for('component.user.verify_email.action', verification_token=token, _full=True)

        email_template_vars = {
            'title': u'Confirm Your User Account',
            'copy': u'Thank you for registering. Please click the following link to complete your registration: <a href="{}">{}</a>'.format(verification_url, verification_url),
        }

        send_email_kwargs = {
            'to_address': user.email_address,
            'subject': u'Confirm Your User Account',
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

        # We log the user in here so that they can continue with possible other registration steps
        # e.g. verifying the account
        request.environ['beaker.session']['user_uid'] = user_uid

        # This overrides the default set by the CRUD handler helper. Need to ensue that we check for the continue url
        # as other components may be relying on it
        if request.GET.get('continue_url', False):
            redirect_url = request.GET['continue_url']
        else:
            redirect_url = webapp2.uri_for('component.user.verify_email.ui',
                                           status_code=self.create_success_status_code)
        response.redirect_to = redirect_url

    def _do_update(self, request, response, form):
        modified = False
        user = appapi.Users.get(resource_uid=form.uid.data)

        if user.first_name != form.first_name.data:
            modified = True
            user.first_name = form.first_name.data

        if user.last_name != form.last_name.data:
            modified = True
            user.last_name = form.last_name.data

        if user.email_address != form.email_address.data:
            modified = True
            user.email_address = form.email_address.data

        if user.language_preference != form.language_preference.data:
            modified = True
            user.language_preference = form.language_preference.data

        if modified:
            appapi.Users.update(resource_object=user)

    def _do_delete(self, request, response, form):
        appapi.Users.delete(resource_uid=form.uid.data)


crud_handlers = UserCRUDHandlers(
    component=component,
    request_config_keys=REQUEST_CONFIG_KEYS,
    filter_params=CRUD_FILTER_PARAMS,
    read_properties=PROPERTY_VIEW_LIST,
    disabled_create_properties=DISABLED_CREATE_PROPERTIES,
    disabled_update_properties=DISABLED_UPDATE_PROPERTIES,
    crud_property_map=PROPERTY_MAP,
    form=UserForm,
    crud_handler_map=CRUD_HANDLER_MAP,
)


class UserSearchHandler(SearchHandler):
    def _do_search(self, request, response, form):
        return appapi.Users.search(query_string=form.query.data,
                                      explicit_query_string_overrides=form.filter_options.filter_expressions,
                                      cursor_support=True,
                                      existing_cursor=form.cursor.data or None,
                                      limit=int(form.sort_options.limit.data),
                                      sort_options=form.sort_options.sort_expressions,)

search_handler = UserSearchHandler(
    component=component,
    search_form=UserSearchForm,
    search_properties=PROPERTY_VIEW_LIST,
    search_property_map=PROPERTY_MAP,
)


def block_if_user(sender, request, response):
    if 'user_uid' in request.environ['beaker.session']:
        raise UserLoggedInException

signal('create.ui.hook').connect(block_if_user, sender=crud_handlers)
signal('pre_create.action.hook').connect(block_if_user, sender=crud_handlers)


INVALID_TOKEN_STATUS_CODE = StatusManager.add_status('Invalid verification token supplied.', 'alert')


def email_verification_holding(request, response):
    parse_request_status_code(request=request, response=response)
    # Check if user is verified. If they are then redirect to logged in home, else show holding page


def verify_email_callback(request, response):
    request_token = request.GET.get('verification_token', None)

    if request_token is None:
        webapp2.abort(400)

    valid, token = appapi.Verification.verify(token=request_token, redirect_uri='component.user.verify_email.action')

    if not valid:
        redirect_url = webapp2.uri_for('component.user.verify_email.ui', status_code=INVALID_TOKEN_STATUS_CODE)
        webapp2.redirect(uri=redirect_url, request=request, response=response)
        return response

    user = appapi.Users.get(resource_uid=token.token_uid)
    user.email_address_verified = True
    appapi.Users.update(resource_object=user)

    redirect_url = webapp2.uri_for('component.user.email_verified.ui')
    webapp2.redirect(uri=redirect_url, request=request, response=response)
    return response


def email_verified(request, response):
    parse_request_status_code(request=request, response=response)
    # TODO: Could maybe show which email address was verified, if a user is logged in

component.add_route(route_type='rendered', route_name='profile', route_title='User Account', handler=crud_handlers.read_ui, page_template='components/extra/read.html')
component.add_route(route_type='rendered', route_name='register', route_title='Register User Account', handler=crud_handlers.create_ui, auto_url_prefix=False, login_required=False)
component.add_route(route_type='action', route_name='create', handler=crud_handlers.create_callback, login_required=False)
component.add_route(route_type='rendered', route_name='update', route_title='Edit User Account', handler=crud_handlers.update_ui, page_template='components/extra/update.html')
component.add_route(route_type='action', route_name='update', handler=crud_handlers.update_callback)
component.add_route(route_type='rendered', route_name='delete', route_title='Delete User Account', handler=crud_handlers.delete_ui, page_template='components/extra/delete.html')
component.add_route(route_type='action', route_name='delete', handler=crud_handlers.delete_callback)

component.add_route(route_type='rendered', route_name='search', route_title='Search', handler=search_handler.search_ui, page_template='components/extra/search.html')

component.add_route(route_type='rendered', route_name='verify_email', route_title='Verify Email Address', handler=email_verification_holding, login_required=False)
component.add_route(route_type='action', route_name='verify_email', handler=verify_email_callback, login_required=False)
component.add_route(route_type='rendered', route_name='email_verified', route_title='Email Address Verified', handler=email_verified, login_required=False)