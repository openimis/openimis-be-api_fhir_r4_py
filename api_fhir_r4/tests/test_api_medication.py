from django.utils.translation import gettext as _
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import R4IdentifierConfig
from fhir.resources.R4B.medication import Medication as FHIRMedication
from api_fhir_r4.converters import MedicationConverter
from api_fhir_r4.tests import GenericFhirAPITestMixin, \
    FhirApiCreateTestMixin, FhirApiUpdateTestMixin, FhirApiReadTestMixin
from api_fhir_r4.configurations import GeneralConfiguration


class MedicationAPITests(GenericFhirAPITestMixin, FhirApiCreateTestMixin, FhirApiUpdateTestMixin, FhirApiReadTestMixin, APITestCase):

    base_url = GeneralConfiguration.get_base_url()+'Medication/'
    _test_json_path = "/test/test_medication.json"
    _TEST_EXPECTED_CODE = "TESTT"

    def setUp(self):
        super(MedicationAPITests, self).setUp()

    def verify_updated_obj(self, updated_obj):
        self.assertTrue(isinstance(updated_obj, FHIRMedication))
        code = MedicationConverter.get_fhir_identifier_by_code(
            updated_obj.identifier,
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        self.assertEqual(self._TEST_EXPECTED_CODE, code)

    def update_resource(self, data):
        data['identifier'][0]["value"] = self._TEST_EXPECTED_CODE

    def update_payload_missing_code_identifier(self, data):
        for i in range(len(data["identifier"])):
            if data["identifier"][i]["type"]["coding"][0]["code"] == "Code":
                del data["identifier"][i]
                return data

    def update_payload_missing_item_name(self, data):
        if "code" in data:
            data.pop("code")
        return data

    def test_post_should_raise_error_no_code_identifier(self):
        self.login()
        self.create_dependencies()
        modified_payload = self.update_payload_missing_code_identifier(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json = response.json()
        splited_output = self.get_response_details(response_json).split(" ")
        self.assertEqual(
            self.get_response_details(response_json),
            _("The request cannot be processed due to the following issues:\nMissing medication `item_code` attribute")
        )

    def test_post_should_raise_error_no_item_name(self):
        self.login()
        self.create_dependencies()
        modified_payload = self.update_payload_missing_item_name(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json = response.json()
        splited_output = self.get_response_details(response_json).split(" ")
        self.assertEqual(
            self.get_response_details(response_json),
            _("The request cannot be processed due to the following issues:\nMissing medication `item_name` attribute")
        )
