import copy

from .utils import PaymentNoticeSerializerUtils
from invoice.services import PaymentInvoiceService


class PaymentNoticeSerializerCreate(object):
    @classmethod
    def create(cls, validated_data, request):
        user = request.user

        imis_payment_detail = validated_data.pop('imis_payment_detail')
        invoice_status = validated_data.pop('invoice_status')

        payment_invoice = copy.deepcopy(validated_data)
        if '_state' in payment_invoice:
            del payment_invoice['_state']
        if '_original_state' in payment_invoice:
            del payment_invoice['_original_state']

        payment_invoice_service = PaymentInvoiceService(user)
        result = payment_invoice_service.create_with_detail(payment_invoice, imis_payment_detail)
        payment_invoice = PaymentNoticeSerializerUtils.get_result_object(result)
        if invoice_status and result['success']:
            # change the invoice status based on 'fhir status'
            PaymentNoticeSerializerUtils.change_invoice_status(payment_invoice_service, payment_invoice)
        return payment_invoice
