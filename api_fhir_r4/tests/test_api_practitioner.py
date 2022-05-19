from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiReadTestMixin
from api_fhir_r4.configurations import GeneralConfiguration
from rest_framework.test import APITestCase


class PractitionerAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase):

    base_url = GeneralConfiguration.get_base_url()+'Practitioner/'
    _test_json_path = "/test/test_claimAdminPractitioner.json"

    def setUp(self):
        super(PractitionerAPITests, self).setUp()
