import logging

from django.core.exceptions import ObjectDoesNotExist

from api_fhir_r4.apps import ApiFhirConfig
from api_fhir_r4.configurations import R4LocationConfig, R4InvoiceConfig, GeneralConfiguration
from api_fhir_r4.converters import PatientConverter, BillInvoiceConverter, InvoiceConverter, \
    HealthFacilityOrganisationConverter
from api_fhir_r4.mapping.invoiceMapping import InvoiceTypeMapping, BillTypeMapping
from api_fhir_r4.subscriptions.notificationManager import RestSubscriptionNotificationManager
from api_fhir_r4.subscriptions.subscriptionCriteriaFilter import SubscriptionCriteriaFilter
from core.service_signals import ServiceSignalBindType
from core.signals import bind_service_signal

from openIMIS.openimisapps import openimis_apps

logger = logging.getLogger('openIMIS')
imis_modules = openimis_apps()


def bind_service_signals():
    if 'insuree' in imis_modules and GeneralConfiguration.get_subscribe_insuree_signal():
        def on_insuree_create_or_update(**kwargs):
            try:
                model = kwargs.get('result', None)
                if model:
                    notify_subscribers(model, PatientConverter(), 'Patient', None)
            except Exception as e:
                logger.error("Error while processing Patient Subscription", exc_info=e)

        bind_service_signal(
            'insuree_service.create_or_update',
            on_insuree_create_or_update,
            bind_type=ServiceSignalBindType.AFTER
        )

    if 'location' in imis_modules and R4LocationConfig.get_subscribe_location_signal():
        def on_hf_create_or_update(**kwargs):
            try:
                model = kwargs.get('result', None)
                if model:
                    notify_subscribers(model, HealthFacilityOrganisationConverter(), 'Organisation', 'bus')
            except Exception as e:
                logger.error("Error while processing Organisation Subscription", exc_info=e)

        bind_service_signal(
            'health_facility_service.update_or_create',
            on_hf_create_or_update,
            bind_type=ServiceSignalBindType.AFTER
        )
    if 'invoice' in imis_modules and R4InvoiceConfig.get_subscribe_invoice_signal():
        from invoice.models import Bill, Invoice

        def on_bill_create(**kwargs):
            try:
                result = kwargs.get('result', {})
                if result and result.get('success', False):
                    model_uuid = result['data']['uuid']
                    model = Bill.objects.get(uuid=model_uuid)
                    notify_subscribers(model, BillInvoiceConverter(), 'Invoice',
                                       BillTypeMapping.invoice_type[model.subject_type.model])
            except Exception as e:
                logger.error("Error while processing Bill Subscription", exc_info=e)

        def on_invoice_create(**kwargs):
            try:
                result = kwargs.get('result', {})
                if result and result.get('success', False):
                    model_uuid = result['data']['uuid']
                    model = Invoice.objects.get(uuid=model_uuid)
                    notify_subscribers(model, InvoiceConverter(), 'Invoice',
                                       InvoiceTypeMapping.invoice_type[model.subject_type.model])
            except Exception as e:
                logger.error("Error while processing Invoice Subscription", exc_info=e)

        bind_service_signal(
            'signal_after_invoice_module_bill_create_service',
            on_bill_create,
            bind_type=ServiceSignalBindType.AFTER
        )
        bind_service_signal(
            'signal_after_invoice_module_invoice_create_service',
            on_invoice_create,
            bind_type=ServiceSignalBindType.AFTER
        )


def notify_subscribers(model, converter, resource_name, resource_type_name):
    try:
        subscriptions = SubscriptionCriteriaFilter(model, resource_name,
                                                   resource_type_name).get_filtered_subscriptions()
        RestSubscriptionNotificationManager(converter).notify_subscribers_with_resource(model, subscriptions)
    except Exception as e:
        logger.error(f'Notifying subscribers failed: {e}')
        import traceback
        logger.debug(traceback.format_exc())
