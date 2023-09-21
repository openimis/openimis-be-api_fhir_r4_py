from api_fhir_r4.configurations import R4PaymentNoticeConfig
from invoice.models import Invoice


class PaymentNoticeStatusMapping:
    _IMIS_ACTIVE_PAYED = Invoice.Status.PAID.value
    _IMIS_ACTIVE_VALIDATED = Invoice.Status.VALIDATED.value
    _IMIS_ACTIVE_SUSPENDED = Invoice.Status.SUSPENDED.value
    _FHIR_ACTIVE_PAYED = R4PaymentNoticeConfig.get_fhir_payment_notice_status_active()
    _FHIR_ACTIVE_VALIDATED = R4PaymentNoticeConfig.get_fhir_payment_notice_status_active()
    _FHIR_ACTIVE_SUSPENDED = R4PaymentNoticeConfig.get_fhir_payment_notice_status_active()

    _IMIS_CANCELLED = Invoice.Status.CANCELLED.value
    _FHIR_CANCELLED = R4PaymentNoticeConfig.get_fhir_payment_notice_status_cancelled()

    _IMIS_DRAFT = Invoice.Status.DRAFT.value
    _FHIR_DRAFT = R4PaymentNoticeConfig.get_fhir_payment_notice_status_draft()

    _IMIS_ENTERED_IN_ERROR = Invoice.Status.DELETED.value
    _FHIR_ENTERED_IN_ERROR = R4PaymentNoticeConfig.get_fhir_payment_notice_status_entered_in_error()

    to_fhir_status = {
        _IMIS_ACTIVE_PAYED: _FHIR_ACTIVE_PAYED,
        _IMIS_ACTIVE_VALIDATED: _FHIR_ACTIVE_VALIDATED,
        _IMIS_ACTIVE_SUSPENDED: _FHIR_ACTIVE_SUSPENDED,
        _IMIS_CANCELLED: _FHIR_CANCELLED,
        _IMIS_DRAFT: _FHIR_DRAFT,
        _IMIS_ENTERED_IN_ERROR: _FHIR_ENTERED_IN_ERROR
    }

    to_imis_status = {
        _FHIR_ACTIVE_PAYED: _IMIS_ACTIVE_PAYED,
        _FHIR_CANCELLED: _IMIS_CANCELLED,
        _FHIR_DRAFT: _IMIS_DRAFT,
        _FHIR_ENTERED_IN_ERROR: _IMIS_ENTERED_IN_ERROR
    }
