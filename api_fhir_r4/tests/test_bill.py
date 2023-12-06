import os

from fhir.resources.R4B.invoice import Invoice

from api_fhir_r4.converters import BillInvoiceConverter
from api_fhir_r4.tests.mixin import ConvertToFhirTestMixin
from api_fhir_r4.tests.mixin.billInvoiceTestMixin import BillInvoiceTestMixin


class InvoiceConverterInvoiceTestCase(BillInvoiceTestMixin, ConvertToFhirTestMixin):
    converter = BillInvoiceConverter
    fhir_resource = Invoice
    json_repr = 'test/test_invoice.json'

    def setUp(self):
        super(InvoiceConverterInvoiceTestCase, self).setUp()

    def test_to_imis_obj(self):
        self.assertRaises(NotImplementedError, self.converter.to_imis_obj, object(), 1)
