from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiReadTestMixin
from rest_framework.test import APITestCase


class OrganisationAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase):
    base_url = GeneralConfiguration.get_base_url() + 'Organization/'
    _test_json_path = None

    def setUp(self):
        super(OrganisationAPITests, self).setUp()
