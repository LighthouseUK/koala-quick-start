# -*- coding: utf-8 -*-
from jerboa.routes import Component
from jerboa.statusmanager import parse_request_status_code

__author__ = 'Matt'


component = Component(name='dashboard', title='Dashboard')


def overview(request, response):
    parse_request_status_code(request=request, response=response)

component.add_route(route_type='rendered', route_name='overview', route_title='Overview', handler=overview, auto_url_prefix=False)
