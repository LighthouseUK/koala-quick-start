import os
import logging
import webapp2
import config
import datetime
import appapi
from beaker.middleware import SessionMiddleware
from jerboa.renderers import retrofit_response, ADD_RESPONSE_VARS_HOOK
from jerboa.routes import RenderedRoute
from jerboa.statusmanager import StatusManager
from jerboa.exceptions import InvalidUserException, UnauthorizedUserException
from jerboa.handlers import custom_dispatcher, custom_adapter, CUSTOM_DISPATCHER_PRE_HOOK, \
    CUSTOM_DISPATCHER_PRE_PROCESS_RESPONSE_HOOK, CUSTOM_DISPATCHER_POST_PROCESS_RESPONSE_HOOK, CLIENT_EXCEPTION_HOOK, \
    CLIENT_404_HOOK, APP_EXCEPTION_HOOK, INVALID_USER_EXCEPTION_HOOK, UNAUTHORIZED_USER_EXCEPTION_HOOK, \
    LOGGED_IN_USER_EXCEPTION_HOOK, default_route


ENDPOINT_NAME = 'AppName'


APP_INFO = {
    'app_name': config.settings.get('app_name', section=ENDPOINT_NAME),
    'title': config.settings.get('title', section=ENDPOINT_NAME),
    'url': config.settings.get('url', section=ENDPOINT_NAME),
    'copyright': config.settings.get('copyright', section=ENDPOINT_NAME),
    'support_email': config.settings.get('support_email', section=ENDPOINT_NAME),
    'support_url': config.settings.get('support_url', section=ENDPOINT_NAME),
}


JINJA2_EXTENSIONS = config.settings.getlist('jinja2_extensions', section=ENDPOINT_NAME)


WEBAPP2_CONFIG = {
    'webapp2_extras.i18n': {
        'translations_path': config.settings.get('i18n_translations_path', section=ENDPOINT_NAME),
    },
    'locales': config.settings.get('i18n_locales', section=ENDPOINT_NAME),
    'i18n_locales': config.settings.get('i18n_locales', section=ENDPOINT_NAME),
    'jinja2_engine_config': {
        'environment_args': {'extensions': JINJA2_EXTENSIONS,
                             'autoescape': config.settings.getboolean('jinja2_env_autoescape', section=ENDPOINT_NAME),},
        'theme_base_template_path': config.settings.getlist('theme_base_template_path', section=ENDPOINT_NAME),
        'theme_compiled_path': config.settings.get('theme_compiled_path', section=ENDPOINT_NAME),
        'enable_i18n': 'jinja2.ext.i18n' in JINJA2_EXTENSIONS,
    },
    'simple_engine_config': {
        'theme_base_template_path': config.settings.get('theme_base_template_path', section=ENDPOINT_NAME),
    },
    'global_renderer_vars': {
        'app_info': APP_INFO,
        'endpoint': config.settings.get('endpoint', section=ENDPOINT_NAME),
        'version': os.environ['CURRENT_VERSION_ID'],
        'theme': config.settings.get('theme', section=ENDPOINT_NAME),
        'base_url': config.settings.get('theme_url', section=ENDPOINT_NAME),
        'css_url': config.settings.get('theme_css_url', section=ENDPOINT_NAME),
        'css_ext': config.settings.get('css_ext', section=ENDPOINT_NAME),
        'js_url': config.settings.get('theme_js_url', section=ENDPOINT_NAME),
        'js_ext': config.settings.get('js_ext', section=ENDPOINT_NAME),
        'common_assets_url': config.settings.get('theme_common_assets_url', section=ENDPOINT_NAME),
        'main_css': config.settings.get('theme_main_css_url', section=ENDPOINT_NAME),
        'base_layout': config.settings.get('theme_base_layout', section=ENDPOINT_NAME),
        'home_route': config.settings.get('home_route', section=ENDPOINT_NAME),
        'user_can': appapi.RBAC.user_can,
        'user_is': appapi.RBAC.user_is,
    },
    'datastore_namespace': config.settings.get('datastore_namespace', section=ENDPOINT_NAME),
    'home_route': config.settings.get('home_route', section=ENDPOINT_NAME),
    'logged_in_home_route': config.settings.get('home_route', section=ENDPOINT_NAME),
    'logged_out_home_route': config.settings.get('login_route', section=ENDPOINT_NAME),
    'unique_user_properties': config.settings.get('unique_user_properties', section=ENDPOINT_NAME),
    'registry_keys': {
        'user': 'user',
        'user_name': 'user_name',
        'user_api_auth': 'user_api_auth',
    }
}


def add_routes(app_instance, route_list):
    from webapp2 import Route
    from webapp2_extras.routes import MultiRoute
    for item in route_list:
        if isinstance(item, (Route, MultiRoute)):
            app_instance.router.add(item)
        else:
            add_routes(app_instance=app_instance, route_list=item)


def get_component_routes():
    import importlib
    _app_routes = []

    # TODO need component types setting, recursively include the routes from each type

    components_base_path = config.settings.get('components_base_path', section=ENDPOINT_NAME)
    enabled_components = config.settings.getlist('enabled_components', section=ENDPOINT_NAME)
    logging.info('Enabled components: [{0}]'.format(','.join(enabled_components)))

    for component in enabled_components:
        imported = importlib.import_module('.{0}'.format(component), components_base_path)
        logging.info('Loading \'{0}\' component.'.format(component))
        _app_routes.append(imported.component.get_routes())

    return _app_routes


sso_frontend = webapp2.WSGIApplication(debug=os.environ['SERVER_SOFTWARE'].startswith('Dev'), config=WEBAPP2_CONFIG)
sso_frontend.router.add(webapp2.Route(template='/', name='default', handler=default_route))
sso_frontend.router.set_dispatcher(custom_dispatcher)
sso_frontend.router.set_adapter(custom_adapter)

add_routes(app_instance=sso_frontend, route_list=get_component_routes())


# Configure the SessionMiddleware
session_opts = {
    'session.type': config.secrets.get('session_type'),
    'session.cookie_expires': config.secrets.getint('session_expires'),
    'session.encrypt_key': config.secrets.get('session_encryption_key'),
    'session.validate_key': config.secrets.get('session_validate_key'),
    'session.secure': False if os.environ['SERVER_NAME'] in ['localhost', '127.0.0.1'] else True,
    'session.httponly': True,
}
app = SessionMiddleware(sso_frontend, session_opts)


logging.info('App Bootstrapped.')


# Below this line is endpoint specific setup. Mainly used for pre or post processing a request or response.
def pre_request_dispatch(sender, request, response):
    request.handler_config = {
        'csrf_config': {
            'csrf_secret': config.secrets.getbyteliteral('csrf_secret'),
            'csrf_time_limit': datetime.timedelta(minutes=config.secrets.getint('csrf_time_limit')),
            'csrf_context': request.environ['beaker.session'],
        },
        'recaptcha_config': {
            'recaptcha_site_key': config.secrets.get('recaptcha_site_key'),
            'recaptcha_site_secret': config.secrets.get('recaptcha_site_secret'),
        },
        'routes': {
            'default': config.settings.get('default_route', section=ENDPOINT_NAME),
            'login': config.settings.get('login_route', section=ENDPOINT_NAME),
            'logout': config.settings.get('logout_route', section=ENDPOINT_NAME),
        },
        'endpoint': ENDPOINT_NAME,
    }

    session = request.environ['beaker.session']

    if getattr(request.route, 'login_required', False) and 'user_uid' not in session:
        raise InvalidUserException

    try:
        user_uid = session['user_uid']
    except KeyError:
        # There is no user to set. If this is the case then we will get exceptions from the handler.
        pass
    else:
        request.user = appapi.Users.get(resource_uid=user_uid)
        if request.GET.get('company_uid', False) and not appapi.RBAC.user_can(user=request.user, action='admin_companies'):
            if not appapi.RBAC.user_can(user=request.user, action='read_company', resource_uid=request.GET['company_uid']):
                raise UnauthorizedUserException('User not allowed access to company')


def add_default_response_vars(sender, request, response):
    # This is a custom hook for the renderer setup. It allows us to set some request specific default template values.
    if isinstance(request.route, RenderedRoute):
        setattr(response.raw, 'route_title', request.route.route_title)
        setattr(response.raw, 'page_template', request.route.page_template)
        setattr(response.raw, 'login_required', request.route.login_required)  # Might be useful for some UI elements?

    response.raw.request = request
    response.raw.logout_uri = str(config.settings.get('logout_route', section=ENDPOINT_NAME))

    try:
        setattr(response.raw, 'session', request.environ['beaker.session'])
    except KeyError:
        pass

    try:
        setattr(response.raw, 'user', request.user)
    except AttributeError:
        pass


def post_request_hook(sender, request, response):
    if isinstance(request.route, RenderedRoute) and response.status_int == 200:
        response.render()
    request.environ['beaker.session'].save()


def client_exception_handler(sender, exception, request, response):
    pass


USER_LOGGED_IN_REDIRECT_STATUS = StatusManager.add_status(message=u'You can\'t visit that page as a logged in user',
                                                          status_type=u'warn')


def logged_in_user_exception_handler(sender, exception, request, response):
    redirect_url = webapp2.uri_for('default', status_code=USER_LOGGED_IN_REDIRECT_STATUS)
    webapp2.redirect(uri=redirect_url, request=request, response=response)


def invalid_user_handler(sender, exception, request, response):
    # if the request was via GET then pass the url to the login handler. If it was POST
    # then we need to drop it - POST requests shouldn't be forwarded.
    if request.method == 'GET':
        continue_url = request.path_qs
    else:
        continue_url = ''

    redirect_url = webapp2.uri_for(request.handler_config['routes']['login'], continue_url=continue_url)
    webapp2.redirect(uri=redirect_url, request=request, response=response)


def unauthorized_user_handler(sender, exception, request, response):
    redirect_url = webapp2.uri_for('default', status_code='403')
    webapp2.redirect(uri=redirect_url, request=request, response=response)


CUSTOM_DISPATCHER_PRE_HOOK.connect(pre_request_dispatch, sender=sso_frontend.router)

# Instead of loading values directly into the response object via the 'CUSTOM_DISPATCHER_PRE_PROCESS_RESPONSE_HOOK',
# we use the retrofit function. It does some initial setup for the renderer and provides a hook to set default
# response vars.
CUSTOM_DISPATCHER_PRE_PROCESS_RESPONSE_HOOK.connect(retrofit_response, sender=sso_frontend.router)
ADD_RESPONSE_VARS_HOOK.connect(add_default_response_vars, sender=sso_frontend.router)

CUSTOM_DISPATCHER_POST_PROCESS_RESPONSE_HOOK.connect(post_request_hook, sender=sso_frontend.router)
# CLIENT_EXCEPTION_HOOK.connect(client_exception_handler, sender=sso_frontend.router)
LOGGED_IN_USER_EXCEPTION_HOOK.connect(logged_in_user_exception_handler, sender=sso_frontend.router)
INVALID_USER_EXCEPTION_HOOK.connect(invalid_user_handler, sender=sso_frontend.router)
UNAUTHORIZED_USER_EXCEPTION_HOOK.connect(unauthorized_user_handler, sender=sso_frontend.router)