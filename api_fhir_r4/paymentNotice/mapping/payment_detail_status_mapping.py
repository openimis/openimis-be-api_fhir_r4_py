from api_fhir_r4.configurations import R4PaymentNoticeConfig
from invoice.models import DetailPaymentInvoice


class PaymentNoticePaymentDetailStatusMapping:
    _IMIS_DETAIL_STATUS_ACCEPTED = DetailPaymentInvoice.DetailPaymentStatus.ACCEPTED
    _FHIR_DETAIL_STATUS_ACTIVE = R4PaymentNoticeConfig.get_fhir_payment_notice_status_active()

    _IMIS_DETAIL_STATUS_CANCELLED = DetailPaymentInvoice.DetailPaymentStatus.CANCELLED
    _FHIR_DETAIL_STATUS_CANCELLED = R4PaymentNoticeConfig.get_fhir_payment_notice_status_cancelled()

    _IMIS_DETAIL_STATUS_REJECTED = DetailPaymentInvoice.DetailPaymentStatus.REJECTED
    _FHIR_DETAIL_STATUS_ENTERED_IN_ERROR = R4PaymentNoticeConfig.get_fhir_payment_notice_status_entered_in_error()

    to_fhir_status = {
        _IMIS_DETAIL_STATUS_ACCEPTED: _FHIR_DETAIL_STATUS_ACTIVE,
        _IMIS_DETAIL_STATUS_CANCELLED: _FHIR_DETAIL_STATUS_CANCELLED,
        _IMIS_DETAIL_STATUS_REJECTED: _FHIR_DETAIL_STATUS_ENTERED_IN_ERROR,
    }

    to_imis_status = {
        _FHIR_DETAIL_STATUS_ACTIVE: _IMIS_DETAIL_STATUS_ACCEPTED,
        _FHIR_DETAIL_STATUS_CANCELLED: _IMIS_DETAIL_STATUS_CANCELLED,
        _FHIR_DETAIL_STATUS_ENTERED_IN_ERROR: _IMIS_DETAIL_STATUS_REJECTED,
    }
