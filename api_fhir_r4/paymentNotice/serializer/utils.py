from rest_framework.exceptions import APIException

from invoice.models import (
    PaymentInvoice,
    DetailPaymentInvoice
)
from invoice.services import PaymentInvoiceService


class PaymentNoticeSerializerUtils(object):
    _ERROR_WHILE_SAVING = 'Error while saving a payment notice: %(msg)s'
    _PAYMENT_CANCEL_STATUS = [
        DetailPaymentInvoice.DetailPaymentStatus.CANCELLED,
        DetailPaymentInvoice.DetailPaymentStatus.REJECTED
    ]

    @classmethod
    def get_result_object(cls, result):
        if result.get('success', False):
            return PaymentInvoice.objects.get(id=result['data']['id'])
        else:
            raise APIException(cls._ERROR_WHILE_SAVING % {'msg': result.get('message', 'Unknown')})

    @classmethod
    def change_invoice_status(
        cls, payment_invoice_service: PaymentInvoiceService, payment: PaymentInvoice
    ):
        payment_detail = DetailPaymentInvoice.objects.filter(payment=payment).first()
        status = payment_detail.status
        if status == DetailPaymentInvoice.DetailPaymentStatus.ACCEPTED:
            payment_invoice_service.payment_received(payment, DetailPaymentInvoice.DetailPaymentStatus.ACCEPTED)
        elif status in cls._PAYMENT_CANCEL_STATUS:
            payment_invoice_service.payment_cancelled(payment)
