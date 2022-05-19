from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiReadTestMixin
from api_fhir_r4.tests.mixin.invoiceTestMixin import InvoiceTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from insuree.models import Insuree


class InvoiceAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase, LogInMixin, InvoiceTestMixin):
    base_url = GeneralConfiguration.get_base_url() + 'Invoice/?resourceType=invoice'
    _test_json_path = "/test/test_invoice.json"

    def setUp(self):
        super(InvoiceAPITests, self).setUp()
        user = self.get_or_create_user_api()
        self.imis_invoice, self.imis_invoice_line_item = self.create_test_imis_instance()
        self.imis_invoice.thirdparty = Insuree.objects.first()
        self.imis_invoice.save(username=user.username)
        self.imis_invoice_line_item.save(username=user.username)
