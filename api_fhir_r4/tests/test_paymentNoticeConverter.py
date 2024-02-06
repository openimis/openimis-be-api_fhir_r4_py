from fhir.resources.R4B.paymentnotice import PaymentNotice

from api_fhir_r4.paymentNotice import PaymentNoticeConverter
from api_fhir_r4.tests.mixin import ConvertJsonToFhirTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from api_fhir_r4.tests.mixin.paymentNoticeTestMixin import PaymentNoticeTestMixin
from invoice.models import (
    Invoice,
    PaymentInvoice,
    DetailPaymentInvoice
)
from invoice.tests.helpers import create_test_invoice


class PaymentNoticeConverterTestCase(PaymentNoticeTestMixin, LogInMixin, ConvertJsonToFhirTestMixin):
    _TEST_USER_NAME = "TestUserTest2"

    converter = PaymentNoticeConverter
    fhir_resource = PaymentNotice
    json_repr = 'test/test_payment_notice.json'

    def create_dependencies(self, user):
        invoice = create_test_invoice(subject=None, thirdparty=None, user=user, **{
            'id': 'bd84b2f2-ec1d-48de-8f8c-5a477aa4a29f',
            'amount_total': '10000.0',
            'amount_net': '10000.0',
            'user_created': user,
            'user_updated': user,
            'date_created': '2020-01-01'
        })
        return invoice

    def test_to_fhir_obj(self):
        user = self.get_or_create_user_api()
        invoice = self.create_dependencies(user)
        imis_payment, imis_payment_detail = self.create_test_imis_instance()
        imis_payment.save(username=user.username)
        imis_payment_detail.payment = imis_payment
        imis_payment_detail.subject = invoice
        imis_payment_detail.save(username=user.username)
        fhir_payment_notice = self.converter.to_fhir_obj(imis_payment)
        self.verify_fhir_instance(fhir_payment_notice)
        self._delete_created_entries(imis_payment, imis_payment_detail, invoice)

    def test_to_imis_obj(self):
        user = self.get_or_create_user_api()
        invoice = self.create_dependencies(user)
        fhir_payment_notice = self.create_test_fhir_instance()
        imis_payment = PaymentNoticeConverter.to_imis_obj(fhir_payment_notice)
        imis_payment.save(username=user.username)
        imis_payment_detail = imis_payment.imis_payment_detail
        imis_payment_detail.payment = imis_payment
        imis_payment_detail.subject = invoice
        if 'reconciliation' in imis_payment.json_ext:
            imis_payment_detail.reconcilation_id = imis_payment.json_ext['reconciliation']['id']
        imis_payment_detail.save(username=user.username)
        imis_invoice_status = imis_payment.invoice_status
        self.verify_imis_instance(imis_payment)
        self.verify_imis_detail_instance(imis_payment, imis_payment_detail)
        self.verify_imis_invoice_status(imis_invoice_status)
        self._delete_created_entries(imis_payment, imis_payment_detail, invoice)

    def _delete_created_entries(self, payment, payment_detail, invoice):
        DetailPaymentInvoice.objects.filter(id=payment_detail.id).delete()
        PaymentInvoice.objects.filter(id=payment.id).delete()
        Invoice.objects.filter(id=invoice.id).delete()
