import logging

from django.core.exceptions import ObjectDoesNotExist

from api_fhir_r4.apps import ApiFhirConfig
from api_fhir_r4.configurations import R4LocationConfig, R4InvoiceConfig, GeneralConfiguration
from api_fhir_r4.converters import PatientConverter, BillInvoiceConverter, InvoiceConverter, \
    HealthFacilityOrganisationConverter
from api_fhir_r4.mapping.invoiceMapping import InvoiceTypeMapping, BillTypeMapping
from api_fhir_r4.subscriptions.notificationManager import RestSubscriptionNotificationManager
from api_fhir_r4.subscriptions.subscriptionCriteriaFilter import SubscriptionCriteriaFilter
from api_fhir_r4.configurations import R4ClaimConfig
from api_fhir_r4.converters import ClaimResponseConverter
from core.service_signals import ServiceSignalBindType
from core.signals import bind_service_signal

from openIMIS.openimisapps import openimis_apps

logger = logging.getLogger('openIMIS')
imis_modules = openimis_apps()
from django.contrib.auth import get_user_model

User = get_user_model()

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

    if 'claim' in imis_modules and R4ClaimConfig.get_subscribe_claim_signal():
        def on_claim_create_or_update(**kwargs):
            """
            Handles notifications when a Claim is created or updated.
            """      
            try:
                model = kwargs.get('result', None)
                try:
                    admin_id = kwargs.get('data')[0][0].get('admin_id')
                    user = User.objects.get(claim_admin_id=admin_id)
                except (User.DoesNotExist, IndexError, KeyError, TypeError):
                    logger.error(f"User with claim_admin_id {admin_id if 'admin_id' in locals() else 'unknown'} not found or invalid data. Aborting notification.")
                    return

                #Instantiate the correct converter (ClaimResponseConverter) with the user
                logger.info(f"Processing subscription for claim {model.uuid} on behalf of user {user.username}")
                converter_instance = ClaimResponseConverter(user=user)                
                logger.debug(f"Processing subscription for created/updated claim: {model.uuid}")
                notify_subscribers(
                    model,
                    converter_instance, # The specific converter for Claims
                    'Claim',          
                    None              
                )
            except Exception as e:
                logger.error("Error while processing Claim Subscription", exc_info=e)

        bind_service_signal(
            'claim.enter_and_submit_claim',
            on_claim_create_or_update,
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
