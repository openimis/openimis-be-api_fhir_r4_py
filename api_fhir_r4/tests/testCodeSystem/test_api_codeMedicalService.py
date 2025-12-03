from rest_framework import status
from rest_framework.test import APITestCase
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.configurations import GeneralConfiguration
from medical.models import Service
from medical.test_helpers import create_test_service


class CodeSystemMedicalServiceAPITests(GenericFhirAPITestMixin, APITestCase):
    base_url = (
        GeneralConfiguration.get_base_url() + "CodeSystem/medical-service/"
    )

    def setUp(self):
        create_test_service("S")
        super(CodeSystemMedicalServiceAPITests, self).setUp()
        self._EXPECTED_COUNT = Service.objects.all().count()

    def test_get_bad_authorization(self):
        response = self.client.get(self.base_url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_should_return_code_system(self):
        self.login()
        response = self.client.get(self.base_url, data=None, format="json")
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service_code = ""
        for concept in response_data["concept"]:
            if concept["display"].startswith("test S service"):
                service_code = concept["code"]
        self.assertTrue(service_code.startswith("TS-"))
        self.assertEqual(response_data["count"], self._EXPECTED_COUNT)
        self.assertEqual(response_data["name"], "MedicalServiceCS")
        self.assertEqual(response_data["title"], "Medical Service")
