from datetime import timedelta

from core.test_helpers import create_test_interactive_user
from django.utils import timezone
from medical.models import Diagnosis
from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration, R4ClaimConfig


class DiagnosisValueSetAPITests(APITestCase):
    base_url = GeneralConfiguration.get_base_url() + "ValueSet/diagnosis/"

    def setUp(self):
        self.user = create_test_interactive_user(
            username="DiagValueSetUser"
        )

    def login(self):
        self.client.force_authenticate(user=self.user)

    @staticmethod
    def create_diagnosis(code, name, validity_to=None):
        return Diagnosis.objects.create(
            code=code,
            name=name,
            validity_to=validity_to,
            audit_user_id=1,
        )

    def test_get_should_require_login(self):
        response = self.client.get(self.base_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_should_return_value_set_definition(self):
        self.login()

        response = self.client.get(self.base_url, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["resourceType"], "ValueSet")
        self.assertEqual(response_data["id"], "diagnosis")
        self.assertEqual(response_data["status"], "active")
        self.assertNotIn("expansion", response_data)
        self.assertTrue(response_data["url"].endswith("ValueSet/diagnosis"))
        self.assertTrue(
            response_data["compose"]["include"][0]["system"].endswith(
                R4ClaimConfig.get_fhir_claim_diagnosis_system()
            )
        )

    def test_expand_should_filter_and_page_diagnoses(self):
        self.create_diagnosis("ZXA01", "Expansion lookup alpha")
        self.create_diagnosis("ZXA02", "Expansion lookup beta")
        self.create_diagnosis("ZXA03", "Different diagnosis")
        self.login()

        response = self.client.get(
            self.base_url + "$expand/",
            {"filter": "EXPANSION LOOKUP", "offset": 1, "count": 1},
            format="json",
        )
        expansion = response.json()["expansion"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(expansion["total"], 2)
        self.assertEqual(expansion["offset"], 1)
        self.assertEqual(len(expansion["contains"]), 1)
        self.assertEqual(expansion["contains"][0]["code"], "ZXA02")
        self.assertIn("system", expansion["contains"][0])

    def test_expand_should_filter_by_code_case_insensitively(self):
        self.create_diagnosis("ZXC01", "Code search diagnosis")
        self.login()

        response = self.client.get(
            self.base_url + "$expand/", {"filter": "zxc01"}, format="json"
        )
        expansion = response.json()["expansion"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(expansion["total"], 1)
        self.assertEqual(expansion["contains"][0]["code"], "ZXC01")

    def test_expand_should_exclude_expired_diagnoses(self):
        self.create_diagnosis(
            "ZXE01",
            "Expired expansion diagnosis",
            validity_to=timezone.now() - timedelta(days=1),
        )
        self.login()

        response = self.client.get(
            self.base_url + "$expand/", {"filter": "ZXE01"}, format="json"
        )
        expansion = response.json()["expansion"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(expansion["total"], 0)
        self.assertEqual(expansion.get("contains", []), [])

    def test_expand_should_reject_invalid_paging_parameters(self):
        self.login()

        response = self.client.get(
            self.base_url + "$expand/", {"count": "invalid"}, format="json"
        )
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["resourceType"], "OperationOutcome")
