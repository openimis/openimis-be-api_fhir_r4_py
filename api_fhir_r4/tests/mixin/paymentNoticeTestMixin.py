from api_fhir_r4.tests import GenericTestMixin
from invoice.models import (
    Invoice,
    PaymentInvoice,
    DetailPaymentInvoice
)


class PaymentNoticeTestMixin(GenericTestMixin):
    _TEST_PAYMENT_NOTICE_IMIS_RECONCILIATION_STATUS = PaymentInvoice.ReconciliationStatus.RECONCILIATED
    _TEST_PAYMENT_NOTICE_IMIS_JSON_EXT = {'reconciliation': {'id': 'id-renconiliation-test-1'}}
    _TEST_PAYMENT_NOTICE_IMIS_DATE_PAYMENT = '2022-05-17'
    _TEST_PAYMENT_NOTICE_IMIS_DATE_CREATED = '2022-05-17T10:58:46.807554'
    _TEST_PAYMENT_NOTICE_IMIS_AMOUNT_RECEIVED = 10000.0
    _TEST_PAYMENT_NOTICE_IMIS_DETAILS_STATUS = DetailPaymentInvoice.DetailPaymentStatus.ACCEPTED
    _TEST_PAYMENT_NOTICE_IMIS_DETAILS_PAYMENT = None
    _TEST_PAYMENT_NOTICE_IMIS_DETAILS_SUBJECT_ID = 'bd84b2f2-ec1d-48de-8f8c-5a477aa4a29f'
    _TEST_PAYMENT_NOTICE_IMIS_DETAILS_RECON_ID = 'id-renconiliation-test-1'

    _TEST_PAYMENT_NOTICE_FHIR_STATUS = 'active'
    _TEST_PAYMENT_NOTICE_FHIR_REQUEST_REFERENCE = 'Invoice/bd84b2f2-ec1d-48de-8f8c-5a477aa4a29f'
    _TEST_PAYMENT_NOTICE_FHIR_REQUEST_REFERENCE_TYPE = 'Invoice'
    _TEST_PAYMENT_NOTICE_FHIR_CREATED = '2022-05-17T10:58:46.807554'
    _TEST_PAYMENT_NOTICE_FHIR_DATE_PAYMENT = '2022-05-17'
    _TEST_PAYMENT_NOTICE_FHIR_PAYMENT_REFERENCE = 'PaymentReconciliation/id-renconiliation-test-1'
    _TEST_PAYMENT_NOTICE_FHIR_RECIPIENT = 'Organization/openIMIS-Implementation'

    _TEST_PAYMENT_NOTICE_FHIR_AMOUNT_VALUE = '10000.0'
    _TEST_PAYMENT_NOTICE_FHIR_AMOUNT_CURRENCY = '$'

    _TEST_PAYMENT_NOTICE_FHIR_PAYMENT_STATUS = 'cleared'

    def create_test_imis_instance(self):
        imis_payment = PaymentInvoice(
            **{
                'reconciliation_status': self._TEST_PAYMENT_NOTICE_IMIS_RECONCILIATION_STATUS,
                'amount_received': self._TEST_PAYMENT_NOTICE_IMIS_AMOUNT_RECEIVED,
                'date_payment': self._TEST_PAYMENT_NOTICE_IMIS_DATE_PAYMENT,
                'json_ext': self._TEST_PAYMENT_NOTICE_IMIS_JSON_EXT,
                'payer_ref': 'ICD-54546'
            }
        )
        self._TEST_PAYMENT_NOTICE_IMIS_DETAILS_PAYMENT = imis_payment
        imis_payment_detail = DetailPaymentInvoice(
            **{
                'status': self._TEST_PAYMENT_NOTICE_IMIS_DETAILS_STATUS,
                'amount': self._TEST_PAYMENT_NOTICE_IMIS_AMOUNT_RECEIVED,
                'payment': self._TEST_PAYMENT_NOTICE_IMIS_DETAILS_PAYMENT,
                'subject_id': self._TEST_PAYMENT_NOTICE_IMIS_DETAILS_SUBJECT_ID
            }
        )
        return imis_payment, imis_payment_detail

    def verify_imis_instance(self, imis_obj):
        self.assertEquals(imis_obj.reconciliation_status, self._TEST_PAYMENT_NOTICE_IMIS_RECONCILIATION_STATUS)
        self.assertEquals(round(float(imis_obj.amount_received),2), round(float(self._TEST_PAYMENT_NOTICE_IMIS_AMOUNT_RECEIVED),2))
        self.assertEquals(f'{imis_obj.date_payment}', self._TEST_PAYMENT_NOTICE_IMIS_DATE_PAYMENT)
        self.assertEquals(imis_obj.json_ext['reconciliation']['id'], self._TEST_PAYMENT_NOTICE_IMIS_JSON_EXT['reconciliation']['id'])
        self.assertEquals(imis_obj.payer_ref, 'PaymentReconciliation/id-renconiliation-test-1')

    def verify_imis_detail_instance(self, imis_obj, imis_detail_obj):
        self.assertEquals(imis_detail_obj.status, self._TEST_PAYMENT_NOTICE_IMIS_DETAILS_STATUS)
        self.assertEquals(imis_detail_obj.amount, self._TEST_PAYMENT_NOTICE_IMIS_AMOUNT_RECEIVED)
        self.assertEquals(imis_detail_obj.payment.id, imis_obj.id)
        self.assertEquals(imis_detail_obj.subject_id, self._TEST_PAYMENT_NOTICE_IMIS_DETAILS_SUBJECT_ID)
        self.assertEquals(imis_detail_obj.reconcilation_id, self._TEST_PAYMENT_NOTICE_IMIS_DETAILS_RECON_ID)

    def verify_imis_invoice_status(self, imis_invoice_status):
        self.assertEquals(imis_invoice_status, Invoice.Status.PAID)

    def create_test_fhir_instance(self):
        return {
            'status': self._TEST_PAYMENT_NOTICE_FHIR_STATUS,
            'request': {
                'reference': self._TEST_PAYMENT_NOTICE_FHIR_PAYMENT_REFERENCE,
                'type': self._TEST_PAYMENT_NOTICE_FHIR_REQUEST_REFERENCE_TYPE
            },
            'created': self._TEST_PAYMENT_NOTICE_FHIR_CREATED,
            'payment': {
                'reference': self._TEST_PAYMENT_NOTICE_FHIR_PAYMENT_REFERENCE
            },
            'paymentDate': self._TEST_PAYMENT_NOTICE_IMIS_DATE_PAYMENT,
            'recipient': {
                'reference': self._TEST_PAYMENT_NOTICE_FHIR_RECIPIENT
            },
            'amount': {
                'value': self._TEST_PAYMENT_NOTICE_FHIR_AMOUNT_VALUE,
                'currency': "$"
            },
            "paymentStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/paymentstatus",
                        "code": self._TEST_PAYMENT_NOTICE_FHIR_PAYMENT_STATUS,
                        "display": self._TEST_PAYMENT_NOTICE_FHIR_PAYMENT_STATUS
                    }
                ]
            }
        }

    def verify_fhir_instance(self, fhir_obj):
        self.assertEquals(fhir_obj.status, self._TEST_PAYMENT_NOTICE_FHIR_STATUS)
        self.assertEquals(fhir_obj.request.reference, self._TEST_PAYMENT_NOTICE_FHIR_REQUEST_REFERENCE)
        self.assertEquals(f'{fhir_obj.paymentDate}', self._TEST_PAYMENT_NOTICE_FHIR_DATE_PAYMENT)
        self.assertEquals(fhir_obj.recipient.reference, self._TEST_PAYMENT_NOTICE_FHIR_RECIPIENT)
        self.assertEquals(round(float(fhir_obj.amount.value),2), round(float(self._TEST_PAYMENT_NOTICE_FHIR_AMOUNT_VALUE),2))
        self.assertEquals(fhir_obj.paymentStatus.coding[0].code, self._TEST_PAYMENT_NOTICE_FHIR_PAYMENT_STATUS)
