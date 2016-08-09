from google.appengine.ext.appstats import recording
from google.appengine.ext import vendor

appstats_CALC_RPC_COSTS = True
appstats_FILTER_LIST = [{'CURRENT_VERSION_ID': '[a-zA-Z\-0-9]*-(prototype|staging|develop).*',}]


def webapp_add_wsgi_middleware(app):
    app = recording.appstats_wsgi_middleware(app)
    return app

# pip install -t thirdparty -r requirements.txt
vendor.add('thirdparty')
