import json
import os

from api_fhir_r4.converters import InvoiceConverter, BillInvoiceConverter
from api_fhir_r4.tests.mixin.billInvoiceTestMixin import BillInvoiceTestMixin
from api_fhir_r4.tests.mixin.invoiceTestMixin import InvoiceTestMixin


class InvoiceConverterInvoiceTestCase(BillInvoiceTestMixin):
    __TEST_INVOICE_JSON_PATH = "/test/test_invoice.json"

    @classmethod
    def setUpClass(cls):
        super(InvoiceConverterInvoiceTestCase, cls).setUpClass()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        cls.__TEST_INVOICE_JSON_TEXT__ = open(dir_path + cls.__TEST_INVOICE_JSON_PATH).read()

    def setUp(self):
        super(InvoiceConverterInvoiceTestCase, self).setUp()

    def test_to_fhir_obj(self):
        imis_invoice = self.create_test_imis_instance()
        fhir_invoice = BillInvoiceConverter.to_fhir_obj(imis_invoice)
        self.verify_fhir_instance(fhir_invoice)

    def test_to_imis_obj(self):
        self.assertRaises(NotImplementedError, InvoiceConverter.to_imis_obj, object(), 1)
