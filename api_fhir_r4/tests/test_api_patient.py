import json
import os
import unittest
from unittest import skip

from django.utils.translation import gettext as _
from fhir.resources.patient import Patient
from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, PatientTestMixin, FhirApiReadTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from insuree.models import Gender
from insuree.test_helpers import create_test_insuree


class PatientAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url() + 'Patient/'
    _test_json_path = "/test/test_patient.json"
    _TEST_LAST_NAME = "TEST_LAST_NAME"
    _TEST_LOCATION_NAME_VILLAGE = "Rachla"
    _TEST_GENDER_CODE = 'M'
    _TEST_EXPECTED_NAME = "UPDATED_NAME"
    _TEST_INSUREE_MOCKED_UUID = "7240daef-5f8f-4b0f-9042-b221e66f184a"
    _TEST_FAMILY_MOCKED_UUID = "8e33033a-9f60-43ad-be3e-3bfeb992aae5"

    _test_json_path_credentials = "/tests/test/test_login.json"
    _test_request_data_credentials = None

    def setUp(self):
        super(PatientAPITests, self).setUp()
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        json_representation = open(dir_path + self._test_json_path_credentials).read()
        self._test_request_data_credentials = json.loads(json_representation)
        self.get_or_create_user_api()

    def verify_updated_obj(self, updated_obj):
        self.assertTrue(isinstance(updated_obj, Patient))
        self.assertEqual(self._TEST_EXPECTED_NAME, updated_obj.name[0].given[0])

    def update_resource(self, data):
        data['name'][0]['given'][0] = self._TEST_EXPECTED_NAME

    def create_dependencies(self):
        gender = Gender()
        gender.code = self._TEST_GENDER_CODE
        gender.save()

        imis_location = PatientTestMixin().create_mocked_location()
        imis_location.save()
        # create mocked insuree with family - new insuree as a part of this test of family
        imis_mocked_insuree = create_test_insuree(with_family=True)
        imis_mocked_insuree.uuid = self._TEST_INSUREE_MOCKED_UUID
        imis_mocked_insuree.current_village = imis_location
        imis_mocked_insuree.last_name = self._TEST_LAST_NAME
        imis_mocked_insuree.save()

        # update family uuid
        imis_family = imis_mocked_insuree.family
        imis_family.uuid = self._TEST_FAMILY_MOCKED_UUID
        imis_family.location = imis_location
        imis_family.save()

    def update_payload_missing_chfid_identifier(self, data):
        for i in range(len(data["identifier"])):
            if data["identifier"][i]["type"]["coding"][0]["code"] == "Code":
                del data["identifier"][i]
                return data

    def update_payload_no_extensions(self, data):
        data["extension"] = []
        return data

    def update_payload_missing_fhir_address_details(self, data, field, kind_of_address):
        for address in data["address"]:
            if address["use"] == kind_of_address:
                address.pop(field)
        return data

    def update_payload_missing_fhir_address_extension(self, data, kind_of_extension):
        for address in data["address"]:
            if address["use"] == "home":
                for i in range(len(address["extension"])):
                    if kind_of_extension in address["extension"][i]['url']:
                        del address["extension"][i]
                        return data

    def update_payload_missing_fhir_address_extensions_all(self, data):
        for address in data["address"]:
            if address["use"] == "home":
                for i in range(len(address["extension"])):
                    address.pop("extension")
                    return data

    def update_payload_fhir_no_address(self, data):
        data["address"] = []
        return data

    def update_payload_fhir_address_no_photo(self, data):
        data.pop("photo")
        return data

    def update_payload_fhir_address_missing_photo_data(self, data):
        for photo in data["photo"]:
            photo.pop("title")
        return data

    def update_payload_fhir_address_no_name(self, data):
        data.pop("name")
        return data

    def update_payload_fhir_address_missing_name_given_field(self, data):
        for name in data["name"]:
            name.pop('given')
        return data

    def test_post_should_create_correctly(self):
        self.create_dependencies()
        response = self.client.post(
            GeneralConfiguration.get_base_url() + 'login/', data=self._test_request_data_credentials, format='json'
        )
        response_json = response.json()
        token = response_json["token"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token}"
        }
        response = self.client.post(self.base_url, data=self._test_request_data, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.content)

    def test_post_should_raise_error_no_chfid_identifier(self):
        self.create_dependencies()
        response = self.client.post(
            GeneralConfiguration.get_base_url() + 'login/', data=self._test_request_data_credentials, format='json'
        )
        response_json = response.json()
        token = response_json["token"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token}"
        }
        modified_payload = self.update_payload_missing_chfid_identifier(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json', **headers)
        response_json = response.json()
        output_error_details = response_json["issue"][0]
        self.assertTrue(response.status_code, 500)
        self.assertTrue('details' in output_error_details.keys())
        self.assertEqual(output_error_details['severity'], 'error')

    def test_post_should_raise_error_no_extensions(self):
        self.login()
        self.create_dependencies()
        modified_payload = self.update_payload_no_extensions(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json = response.json()
        self.assertEqual(
            response_json["issue"][0]["details"]["text"],
            _("At least one extension with is_head is required")
        )

    def test_post_should_raise_missing_fhir_home_address_details(self):
        self.login()
        self.create_dependencies()
        # missing city
        self._assert_filed_mandatory('city')
        self._assert_filed_mandatory('district')
        self._assert_filed_mandatory('state')

    def test_post_should_raise_missing_fhir_address_home_family_extensions(self):
        self.login()
        self.create_dependencies()
        # missing municipality extension
        modified_payload = self.update_payload_missing_fhir_address_extension(
            data=self._test_request_data, kind_of_extension='address-municipality')
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json_municipality = response.json()
        # missing all extensions
        modified_payload = self.update_payload_missing_fhir_address_extensions_all(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json_no_extensions = response.json()
        self.assertIn(
            "FHIR Patient address without address-municipality reference.",
            response_json_municipality["issue"][0]["details"]["text"],
        )

        self.assertEqual(
            response_json_no_extensions["issue"][0]["details"]["text"],
            _("Missing extensions for Address")
        )

    @skip("This test needs to be checked. Isnuree without family can have no address")
    def test_post_should_raise_error_no_address(self):
        self.login()
        self.create_dependencies()
        modified_payload = self.update_payload_fhir_no_address(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json = response.json()
        self.assertEqual(
            response_json["issue"][0]["details"]["text"],
            _('Address must be supported')
        )

    @skip("This test needs to be checked. At the moment photo is not obligatory")
    def test_post_should_raise_error_no_photo(self):
        self.login()
        self.create_dependencies()
        modified_payload = self.update_payload_fhir_address_no_photo(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json = response.json()
        self.assertEqual(
            response_json["issue"][0]["details"]["text"],
            _('FHIR Patient without photo data.')
        )

    def test_post_should_raise_error_missing_photo_data(self):
        self.login()
        self.create_dependencies()
        modified_payload = self.update_payload_fhir_address_missing_photo_data(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json = response.json()
        self.assertEqual(
            response_json["issue"][0]["details"]["text"],
            _('FHIR Patient misses one of required fields:  contentType, title, creation')
        )

    def test_post_should_raise_error_missing_name_attribute(self):
        self.login()
        self.create_dependencies()
        modified_payload = self.update_payload_fhir_address_missing_name_given_field(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json_no_given_name = response.json()
        self.assertEqual(
            response_json_no_given_name["issue"][0]["details"]["text"],
            _('Missing obligatory fields for fhir patient name: family or given')
        )
        modified_payload = self.update_payload_fhir_address_no_name(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json_no_name = response.json()
        self.assertEqual(
            response_json_no_name["issue"][0]["details"]["text"],
            _('Missing fhir patient attribute: name')
        )

    def _assert_filed_mandatory(self, field):
        modified_payload = self.update_payload_missing_fhir_address_details(
            data=self._test_request_data, field=field, kind_of_address="home")
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        json_response = response.json()

        # Missing mandatory field should result in operation failure.
        self.assertEqual(response.status_code, 500)
        # Information regarding failure reason should be provided
        self.assertIsNotNone(json_response["issue"][0]["details"]["text"])
        # Information regarding field should be part of failure reason
        self.assertIn(field, json_response["issue"][0]["details"]["text"])

