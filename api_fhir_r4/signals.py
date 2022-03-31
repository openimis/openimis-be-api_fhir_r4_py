import logging

from django.core.exceptions import ObjectDoesNotExist

from api_fhir_r4.converters import PatientConverter, BillInvoiceConverter, InvoiceConverter
from api_fhir_r4.subscriptions.notificationManager import RestSubscriptionNotificationManager
from api_fhir_r4.subscriptions.subscriptionCriteriaFilter import SubscriptionCriteriaFilter
from core.service_signals import ServiceSignalBindType
from core.signals import bind_service_signal
from invoice.models import Bill, Invoice

logger = logging.getLogger('openIMIS')


def bind_service_signals():
    bind_service_signal(
        'insuree_service.create_or_update',
        on_insuree_create_or_update,
        bind_type=ServiceSignalBindType.AFTER
    )
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


def on_insuree_create_or_update(**kwargs):
    model = kwargs.get('result', None)
    if model:
        notify_subscribers(model, PatientConverter(), 'Patient')


def on_bill_create(**kwargs):
    if kwargs.get('result', {}).get('success', False):
        model_uuid = kwargs['result']['data']['uuid']
        try:
            model = Bill.objects.get(uuid=model_uuid)
            notify_subscribers(model, BillInvoiceConverter(), 'Bill')
        except ObjectDoesNotExist:
            logger.error(f'Bill returned from service does not exists ({model_uuid})')
            import traceback
            logger.debug(traceback.format_exc())


def on_invoice_create(**kwargs):
    if kwargs.get('result', {}).get('success', False):
        model_uuid = kwargs['result']['data']['uuid']
        try:
            model = Invoice.objects.get(uuid=model_uuid)
            notify_subscribers(model, InvoiceConverter(), 'Invoice')
        except ObjectDoesNotExist:
            logger.error(f'Invoice returned from service does not exists ({model_uuid})')
            import traceback
            logger.debug(traceback.format_exc())


def notify_subscribers(model, converter, resource_type):
    try:
        subscriptions = SubscriptionCriteriaFilter(model, resource_type).get_filtered_subscriptions()
        RestSubscriptionNotificationManager(converter).notify_subscribers_with_resource(model, subscriptions)
    except Exception as e:
        logger.error(f'Notifying subscribers failed: {e}')
        import traceback
        logger.debug(traceback.format_exc())
