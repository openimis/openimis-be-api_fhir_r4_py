from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiReadTestMixin
from api_fhir_r4.configurations import GeneralConfiguration
from rest_framework.test import APITestCase


class PractitionerRoleAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase):

    base_url = GeneralConfiguration.get_base_url()+'PractitionerRole/'
    _test_json_path = "/test/test_claimAdminPractitionerRole.json"

    def setUp(self):
        super(PractitionerRoleAPITests, self).setUp()
