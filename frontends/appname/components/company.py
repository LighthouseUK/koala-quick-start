# -*- coding: utf-8 -*-
import appapi
from jerboa.routes import Component
# For forms
import wtforms
from jerboa.extra import CrudHandler, SearchHandler
from jerboa.utils import eu_country, US_STATES_TUPLE
from webapp2_extras.i18n import _lazy as _
from jerboa.forms import BaseModelForm, BaseSearchForm, GAEFilterOptions, FormField, DEFAULT_NONE_VALUE, \
    CountryCodeValidationWithDefaultSupport, CountryCodeValidation, GAESearchCursorMixin, GAESortOptions, \
    ExtendedSelectField, BOOLEAN_VALUE_TUPLE, AddressMixin, FIELD_MAXLENGTH, EMAIL_REGEXP, MOBILE_REGEXP, \
    ADDRESS_MAXLENGTH, CITY_MAXLENGTH, UK_COUNTIES_TUPLE, STATIC_COUNTRY_LABLES_TUPLE, PHONE_MAXLENGTH, \
    strip_whitespace_filter, MobileValidator, DeliveryUKCountyValidation, BillingUKCountyValidation, \
    BillingUKPostCodeValidation, DeliveryUSStateValidation, BillingUSStateValidation


__author__ = 'Matt Badger'


component = Component(name='company', title='Company')

REQUEST_CONFIG_KEYS = [u'csrf_config']

COMPANY_PROPERTY_VIEW_LIST = [
    u'company_name',
    u'contact_first_name',
    u'contact_last_name',
    u'contact_email',
    u'contact_phone',
    u'contact_mobile',
    u'delivery_address_1',
    u'delivery_address_2',
    u'delivery_address_3',
    u'delivery_city',
    u'delivery_state',
    u'delivery_county',
    u'delivery_post_code',
    u'delivery_country',
    u'billing_address_1',
    u'billing_address_2',
    u'billing_address_3',
    u'billing_city',
    u'billing_state',
    u'billing_county',
    u'billing_post_code',
    u'billing_country',
]

COMPANY_DISABLED_CREATE_PROPERTIES = [
    u'uid',
]


def ContactUKPostCodeValidation(form, field):
    if not len(field.data) > 0 and form.delivery_country.data == 'GB':
        raise wtforms.validators.ValidationError('Contact Post code is a required field for entrants in the UK.')


class CompanyForm(BaseModelForm):
    company_name = wtforms.fields.StringField(_('Company Name'), [
        wtforms.validators.InputRequired(),
        wtforms.validators.Length(max=FIELD_MAXLENGTH,
                                  message=_("Company name cannot be longer than %(max)d characters.")),
    ])

    contact_first_name = wtforms.fields.StringField(_('Contact First Name'), [
        wtforms.validators.InputRequired(),
        wtforms.validators.Length(max=20, message=_("First name cannot be longer than %(max)d characters.")),
    ])

    contact_last_name = wtforms.fields.StringField(_('Contact Last Name'), [
        wtforms.validators.InputRequired(),
        wtforms.validators.Length(max=20, message=_("Last name cannot be longer than %(max)d characters.")),
    ])

    contact_email = wtforms.fields.StringField(_('Contact Email'), [
        wtforms.validators.InputRequired(),
        wtforms.validators.Length(max=FIELD_MAXLENGTH,
                                  message=_("Email address must be less than between %(max)d characters long.")),
        wtforms.validators.regexp(EMAIL_REGEXP, message=_('Invalid characters found in contact email address.'))
    ])

    contact_phone = wtforms.fields.StringField(_('Contact Telephone'), [
            wtforms.validators.InputRequired(),
            wtforms.validators.Length(max=PHONE_MAXLENGTH,
                                      message=_("Phone number must be less than %(max)d characters long.")),
            wtforms.validators.regexp(MOBILE_REGEXP, message=_('Invalid characters found in phone number.'))
    ], filters=[strip_whitespace_filter])

    contact_mobile = wtforms.fields.StringField(_('Contact Mobile'), [MobileValidator], filters=[strip_whitespace_filter])

    # Delivery Address
    delivery_country = wtforms.fields.SelectField(_('Contact Country'), [
        CountryCodeValidation,
        wtforms.validators.InputRequired(),
        wtforms.validators.Length(max=2, message=_("Country code must be %(max)d characters.")),
    ], choices=STATIC_COUNTRY_LABLES_TUPLE, default='GB')
    delivery_address_1 = wtforms.fields.StringField(_('Contact Address 1'), [
        wtforms.validators.InputRequired(),
        wtforms.validators.Length(max=ADDRESS_MAXLENGTH,
                                  message=_("Address 1 cannot be longer than %(max)d characters.")),
    ])
    delivery_address_2 = wtforms.fields.StringField(_('Contact Address 2'), [
        wtforms.validators.Length(max=ADDRESS_MAXLENGTH,
                                  message=_("Address 2 cannot be longer than %(max)d characters.")),
    ])
    delivery_address_3 = wtforms.fields.StringField(_('Contact Address 3'), [
        wtforms.validators.Length(max=ADDRESS_MAXLENGTH,
                                  message=_("Address 3 cannot be longer than %(max)d characters.")),
    ])
    delivery_city = wtforms.fields.StringField(_('Contact City'), [
        wtforms.validators.InputRequired(),
        wtforms.validators.Length(max=CITY_MAXLENGTH,
                                  message=_("City cannot be longer than %(max)d characters.")),
    ])
    delivery_state = wtforms.fields.SelectField(_('Contact State (Required for US companies)'), [
        DeliveryUSStateValidation,
    ], choices=US_STATES_TUPLE)
    delivery_county = ExtendedSelectField(_('Contact County (Required for UK companies)'), [
        DeliveryUKCountyValidation,
    ], choices=UK_COUNTIES_TUPLE)
    delivery_post_code = wtforms.fields.StringField(_('Contact Post Code/Zip Code (Required for UK companies)'), [
        ContactUKPostCodeValidation,
    ])

    # Billing Address
    billing_country = wtforms.fields.SelectField(_('Billing Country'), [
        CountryCodeValidation,
        wtforms.validators.InputRequired(),
        wtforms.validators.Length(max=2, message=_("Country code must be %(max)d characters.")),
    ], choices=STATIC_COUNTRY_LABLES_TUPLE, default='GB')
    billing_address_1 = wtforms.fields.StringField(_('Billing Address 1'), [
        wtforms.validators.InputRequired(),
        wtforms.validators.Length(max=ADDRESS_MAXLENGTH,
                                  message=_("Address 1 cannot be longer than %(max)d characters.")),
    ])
    billing_address_2 = wtforms.fields.StringField(_('Billing Address 2'), [
        wtforms.validators.Length(max=ADDRESS_MAXLENGTH,
                                  message=_("Address 2 cannot be longer than %(max)d characters.")),
    ])
    billing_address_3 = wtforms.fields.StringField(_('Billing Address 3'), [
        wtforms.validators.Length(max=ADDRESS_MAXLENGTH,
                                  message=_("Address 3 cannot be longer than %(max)d characters.")),
    ])
    billing_city = wtforms.fields.StringField(_('Billing City'), [
        wtforms.validators.InputRequired(),
        wtforms.validators.Length(max=CITY_MAXLENGTH,
                                  message=_("City cannot be longer than %(max)d characters.")),
    ])
    billing_state = wtforms.fields.SelectField(_('Billing State (Required for US companies)'), [
        BillingUSStateValidation,
    ], choices=US_STATES_TUPLE)
    billing_county = ExtendedSelectField(_('Billing County (Required for UK companies)'), [
        BillingUKCountyValidation,
    ], choices=UK_COUNTIES_TUPLE)
    billing_post_code = wtforms.fields.StringField(_('Billing Post Code/Zip Code (Required for UK companies)'), [
        BillingUKPostCodeValidation,
    ])


class CompanyCRUDHandlers(CrudHandler):
    def _load_model(self, uid):
        return appapi.Companies.get(resource_uid=uid)

    def _do_create(self, request, response, form):
        company_kwargs = {
            'company_name': form.company_name.data,
            'contact_first_name': form.contact_first_name.data,
            'contact_last_name': form.contact_last_name.data,
            'contact_email': form.contact_email.data,
            'contact_phone': form.contact_phone.data,
            'contact_mobile': form.contact_mobile.data,
            'delivery_address_1': form.delivery_address_1.data,
            'delivery_address_2': form.delivery_address_2.data,
            'delivery_address_3': form.delivery_address_3.data,
            'delivery_city': form.delivery_city.data,
            'delivery_post_code': form.delivery_post_code.data,
            'delivery_country': form.delivery_country.data,
            'billing_address_1': form.billing_address_1.data,
            'billing_address_2': form.billing_address_2.data,
            'billing_address_3': form.billing_address_3.data,
            'billing_city': form.billing_city.data,
            'billing_post_code': form.billing_post_code.data,
            'billing_country': form.billing_country.data,
        }

        if form.delivery_country.data == 'GB':
            company_kwargs['delivery_county'] = form.delivery_county.data
            company_kwargs['delivery_state'] = None
        elif form.delivery_country.data == 'US':
            company_kwargs['delivery_state'] = form.delivery_state.data
            company_kwargs['delivery_county'] = None

        if form.billing_country.data == 'GB':
            company_kwargs['billing_county'] = form.billing_county.data
            company_kwargs['billing_state'] = None
        elif form.billing_country.data == 'US':
            company_kwargs['billing_state'] = form.billing_state.data
            company_kwargs['billing_county'] = None

        company = appapi.Companies.new(**company_kwargs)
        response.raw.created_uid = appapi.Companies.insert(resource_object=company)

    def _do_update(self, request, response, form):
        company = appapi.Companies.get(resource_uid=form.uid.data)

        company_patch = {}
        delivery_county = None
        delivery_state = None
        billing_county = None
        billing_state = None

        if form.delivery_country.data == 'GB':
            # Allow county only, otherwise blank
            if company.delivery_county != form.delivery_county.data:
                delivery_county = form.delivery_county.data
            else:
                delivery_county = company.delivery_county

        if form.billing_country.data == 'GB':
            # Allow county only, otherwise blank
            if company.billing_county != form.billing_county.data:
                billing_county = form.billing_county.data
            else:
                billing_county = company.billing_county

        if form.delivery_country.data == 'US':
            # Allow state only, otherwise blank
            if company.delivery_state != form.delivery_state.data:
                delivery_state = form.delivery_state.data
            else:
                delivery_state = company.delivery_state

        if form.billing_country.data == 'US':
            # Allow state only, otherwise blank
            if company.billing_state != form.billing_state.data:
                billing_state = form.billing_state.data
            else:
                billing_state = company.billing_state

        if company.company_name != form.company_name.data:
            company_patch['company_name'] = form.company_name.data

        if company.contact_first_name != form.contact_first_name.data:
            company_patch['contact_first_name'] = form.contact_first_name.data

        if company.contact_last_name != form.contact_last_name.data:
            company_patch['contact_last_name'] = form.contact_last_name.data

        if company.contact_email != form.contact_email.data:
            company_patch['contact_email'] = form.contact_email.data

        if company.contact_phone != form.contact_phone.data:
            company_patch['contact_phone'] = form.contact_phone.data

        if company.contact_mobile != form.contact_mobile.data:
            company_patch['contact_mobile'] = form.contact_mobile.data

        if company.delivery_address_1 != form.delivery_address_1.data:
            company_patch['delivery_address_1'] = form.delivery_address_1.data

        if company.delivery_address_2 != form.delivery_address_2.data:
            company_patch['delivery_address_2'] = form.delivery_address_2.data

        if company.delivery_address_3 != form.delivery_address_3.data:
            company_patch['delivery_address_3'] = form.delivery_address_3.data

        if company.delivery_city != form.delivery_city.data:
            company_patch['delivery_city'] = form.delivery_city.data

        if company.delivery_county != delivery_county:
            company_patch['delivery_county'] = delivery_county

        if company.delivery_state != delivery_state:
            company_patch['delivery_state'] = delivery_state

        if company.delivery_post_code != form.delivery_post_code.data:
            company_patch['delivery_post_code'] = form.delivery_post_code.data

        if company.delivery_country != form.delivery_country.data:
            company_patch['delivery_country'] = form.delivery_country.data

        if company.billing_address_1 != form.billing_address_1.data:
            company_patch['billing_address_1'] = form.billing_address_1.data

        if company.billing_address_2 != form.billing_address_2.data:
            company_patch['billing_address_2'] = form.billing_address_2.data

        if company.billing_address_3 != form.billing_address_3.data:
            company_patch['billing_address_3'] = form.billing_address_3.data

        if company.billing_city != form.billing_city.data:
            company_patch['billing_city'] = form.billing_city.data

        if company.billing_county != billing_county:
            company_patch['billing_county'] = billing_county

        if company.billing_state != billing_state:
            company_patch['billing_state'] = billing_state

        if company.billing_post_code != form.billing_post_code.data:
            company_patch['billing_post_code'] = form.billing_post_code.data

        if company.billing_country != form.billing_country.data:
            company_patch['billing_country'] = form.billing_country.data

        if company_patch:
            appapi.Companies.patch(resource_uid=form.uid.data, delta_update=company_patch)

        self.set_redirect_url(request=request, response=response, handler='update_success',
                              status_code=self.update_success_status_code, follow_continue=True)

    def _do_delete(self, request, response, form):
        appapi.Companies.delete(resource_uid=form.uid.data)


company_crud_handlers = CompanyCRUDHandlers(
    component=component,
    request_config_keys=REQUEST_CONFIG_KEYS,
    read_properties=COMPANY_PROPERTY_VIEW_LIST,
    disabled_create_properties=COMPANY_DISABLED_CREATE_PROPERTIES,
    form=CompanyForm,
    # crud_handler_map=COMPANY_HANDLER_MAP,
    force_create_ui_get_data=True,
)


component.add_route(route_type='rendered', route_name='read', route_title='Company Profile', handler=company_crud_handlers.read_ui, page_template='components/extra/read.html')
component.add_route(route_type='rendered', route_name='create', route_title='Create Company Profile', handler=company_crud_handlers.create_ui, page_template='components/extra/create.html')
component.add_route(route_type='rendered', route_name='update', route_title='Edit Company Profile', handler=company_crud_handlers.update_ui, page_template='components/extra/update.html')
component.add_route(route_type='action', route_name='create', handler=company_crud_handlers.create_callback)
component.add_route(route_type='action', route_name='update', handler=company_crud_handlers.update_callback)