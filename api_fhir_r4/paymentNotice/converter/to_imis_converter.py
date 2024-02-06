from django.contrib.contenttypes.models import ContentType
from fhir.resources.R4B.paymentnotice import PaymentNotice

from .errors import (
    ERROR_BAD_STATUS,
    ERROR_BAD_PAYMENT_STATUS,
    ERROR_BAD_TYPE_REQUEST
)
from api_fhir_r4.converters import (
    BaseFHIRConverter,
    ReferenceConverterMixin
)
from api_fhir_r4.paymentNotice.mapping import (
    PaymentNoticeStatusMapping,
    PaymentNoticePaymentDetailStatusMapping,
    PaymentNoticePaymentStatusMapping
)
from invoice.models import (
    PaymentInvoice,
    DetailPaymentInvoice
)

PAYMENT_STATUS = ['cleared', 'paid']
STATUS = ['active', 'cancelled', 'draft', 'entered-in-error']
SUBJECT_TYPE = ['bill', 'invoice']


class PaymentNoticeToImisConverter(BaseFHIRConverter, ReferenceConverterMixin):
    @classmethod
    def to_imis_obj(cls, fhir_payment_notice, audit_user_id=None):
        errors = []
        fhir_payment_notice = PaymentNotice(**fhir_payment_notice)
        imis_payment = PaymentInvoice()
        imis_payment_detail = DetailPaymentInvoice()
        cls.build_imis_payment_date_created(imis_payment, imis_payment_detail, fhir_payment_notice)
        cls.build_imis_payment_payer_ref(imis_payment,fhir_payment_notice)
        cls.build_imis_payment_reconciliation_status(imis_payment, fhir_payment_notice, errors)
        cls.build_imis_payment_amount(imis_payment, imis_payment_detail, fhir_payment_notice)
        cls.build_imis_payment_date_payment(imis_payment, fhir_payment_notice)
        cls.build_imis_payment_json_ext(imis_payment, fhir_payment_notice)
        cls.build_imis_payment_detail_invoice(imis_payment_detail, fhir_payment_notice, errors)
        cls.build_imis_payment_detail_status(imis_payment_detail, fhir_payment_notice, errors)
        invoice_status = None
        if imis_payment_detail.subject_id:
            invoice_status = cls.get_imis_invoice_status(fhir_payment_notice, errors)
        cls.check_errors(errors)
        imis_payment.imis_payment_detail = imis_payment_detail
        imis_payment.invoice_status = invoice_status
        return imis_payment
    @classmethod
    def build_imis_payment_payer_ref(cls, imis_payment, fhir_payment_notice):
        imis_payment.payer_ref = fhir_payment_notice.payment.reference

    @classmethod
    def build_imis_payment_date_created(cls, imis_payment, imis_payment_detail, fhir_payment_notice):
        created = fhir_payment_notice.created
        imis_payment.date_created = created
        imis_payment.date_updated = created
        imis_payment_detail.date_created = created
        imis_payment_detail.date_updated = created

    @classmethod
    def build_imis_payment_reconciliation_status(cls, imis_payment, fhir_payment_notice, errors):
        coding = cls.get_first_coding_from_codeable_concept(fhir_payment_notice.paymentStatus)
        payment_status = coding.code
        if payment_status in PAYMENT_STATUS:
            imis_payment.reconciliation_status = PaymentNoticePaymentStatusMapping\
                .to_imis_status[payment_status]
        else:
            errors.append(ERROR_BAD_PAYMENT_STATUS)

    @classmethod
    def get_imis_invoice_status(cls, fhir_payment_notice, errors):
        status = fhir_payment_notice.status
        if status in STATUS:
            invoice_status = PaymentNoticeStatusMapping \
                .to_imis_status[status]
            return invoice_status
        else:
            errors.append(ERROR_BAD_STATUS)
            return None

    @classmethod
    def build_imis_payment_detail_status(cls, imis_payment_detail, fhir_payment_notice, errors):
        if fhir_payment_notice.status in STATUS:
            imis_payment_detail.status = PaymentNoticePaymentDetailStatusMapping.\
                to_imis_status[fhir_payment_notice.status]
        else:
            errors.append(ERROR_BAD_STATUS)

    @classmethod
    def build_imis_payment_json_ext(cls, imis_payment, fhir_payment_notice):
        # for saving PaymentReconciliation in json_ext
        reconciliation_id = cls.get_id_from_reference(fhir_payment_notice.payment)
        imis_payment.json_ext = {'reconciliation': {'id': reconciliation_id}}

    @classmethod
    def build_imis_payment_detail_invoice(cls, imis_payment_detail, fhir_payment_notice, errors):
        subject_id = cls.get_id_from_reference(fhir_payment_notice.request)
        subject_type = fhir_payment_notice.request.type.lower()
        if subject_type in SUBJECT_TYPE:
            imis_payment_detail.subject_type = cls._convert_content_type(subject_type)
            imis_payment_detail.subject_id = subject_id
        else:
            errors.append(ERROR_BAD_TYPE_REQUEST)
        

    @classmethod
    def _convert_content_type(cls, subject_type):
        return ContentType.objects.get(model__iexact=subject_type)

    @classmethod
    def build_imis_payment_amount(cls, imis_payment, imis_payment_detail, fhir_payment_notice):
        amount = fhir_payment_notice.amount.value
        imis_payment.amount_received = amount
        imis_payment_detail.amount = amount

    @classmethod
    def build_imis_payment_date_payment(cls, imis_payment, fhir_payment_notice):
        payment_date = fhir_payment_notice.paymentDate
        imis_payment.date_payment = payment_date
