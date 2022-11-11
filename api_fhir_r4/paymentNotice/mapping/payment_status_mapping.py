from api_fhir_r4.configurations import R4PaymentNoticeConfig
from invoice.models import PaymentInvoice


class PaymentNoticePaymentStatusMapping:
    _IMIS_RECONCILIATED_CLEARED = PaymentInvoice.ReconciliationStatus.RECONCILIATED.value
    _FHIR_RECONCILIATED_CLEARED = R4PaymentNoticeConfig.get_fhir_payment_notice_payment_status_cleared()

    _IMIS_NOT_RECONCILIATED_PAID = PaymentInvoice.ReconciliationStatus.NOT_RECONCILIATED.value
    _FHIR_NOT_RECONCILIATED_PAID = R4PaymentNoticeConfig.get_fhir_payment_notice_payment_status_paid()

    to_fhir_status = {
        _IMIS_RECONCILIATED_CLEARED: _FHIR_RECONCILIATED_CLEARED,
        _IMIS_NOT_RECONCILIATED_PAID: _FHIR_NOT_RECONCILIATED_PAID,
    }

    to_imis_status = {
        _FHIR_RECONCILIATED_CLEARED: _IMIS_RECONCILIATED_CLEARED,
        _FHIR_NOT_RECONCILIATED_PAID: _IMIS_NOT_RECONCILIATED_PAID,
    }
