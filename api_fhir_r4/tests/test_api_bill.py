from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiReadTestMixin
from rest_framework.test import APITestCase


class InvoiceAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase):
    base_url = GeneralConfiguration.get_base_url() + 'Invoice/?resourceType=bill'
    _test_json_path = "/test/test_invoice.json"

    def setUp(self):
        super(InvoiceAPITests, self).setUp()
