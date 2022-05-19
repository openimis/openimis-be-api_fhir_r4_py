from fhir.resources.invoice import Invoice

from api_fhir_r4.converters import InvoiceConverter
from api_fhir_r4.tests.mixin import ConvertJsonToFhirTestMixin
from api_fhir_r4.tests.mixin.invoiceTestMixin import InvoiceTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin


class InvoiceConverterTestCase(InvoiceTestMixin, LogInMixin, ConvertJsonToFhirTestMixin):
    _TEST_USER_NAME = "TestUserTest2"

    converter = InvoiceConverter
    fhir_resource = Invoice
    json_repr = 'test/test_invoice.json'

    def test_to_fhir_obj(self):
        user = self.get_or_create_user_api()
        imis_invoice, imis_invoice_line_item = self.create_test_imis_instance()
        imis_invoice.save(username=user.username)
        imis_invoice_line_item.save(username=user.username)
        fhir_invoice = self.converter.to_fhir_obj(imis_invoice)
        self.verify_fhir_instance(fhir_invoice)

    def test_to_imis_obj(self):
        self.assertRaises(NotImplementedError, InvoiceConverter.to_imis_obj, object(), 1)
