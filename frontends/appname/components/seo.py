# -*- coding: utf-8 -*-
from jerboa.routes import Component


__author__ = 'Matt Badger'


component = Component(name='seo', title='Seo')


def robots(request, response):
    pass


def humans(request, response):
    pass


def sitemap(request, response):
    response.raw.scheme = request.scheme
    response.raw.host = request.host


def cross_domain(request, response):
    response.raw.scheme = request.scheme
    response.raw.host = request.host


component.add_route(route_type='rendered', route_name='robots', handler=robots, template_engine='simple', content_type='txt', strip_type=False, auto_url_prefix=False, login_required=False)
component.add_route(route_type='rendered', route_name='humans', handler=humans, template_engine='simple', content_type='txt', strip_type=False, auto_url_prefix=False, login_required=False)
component.add_route(route_type='rendered', route_name='sitemap', handler=sitemap, template_engine='simple', content_type='xml', strip_type=False, auto_url_prefix=False, login_required=False)
component.add_route(route_type='rendered', route_name='crossdomain', handler=cross_domain, template_engine='simple', content_type='xml', strip_type=False, auto_url_prefix=False, login_required=False)
