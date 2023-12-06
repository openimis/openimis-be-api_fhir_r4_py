import json
import os

from django.utils.translation import gettext as _
from fhir.resources.R4B.group import Group
from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiReadTestMixin, LocationTestMixin 
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from insuree.test_helpers import *
from api_fhir_r4.tests.utils import load_and_replace_json


class GroupAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url() + 'Group/'
    _test_json_path = "/test/test_group.json"
    _TEST_INSUREE_CHFID = "TestChfId1"
    _TEST_INSUREE_UUID = "01916024-20a9-45ba-a295-019ab0830000"
    _TEST_INSUREE_LAST_NAME = "Test"
    _TEST_INSUREE_OTHER_NAMES = "TestInsuree"
    _TEST_POVERTY_STATUS = True
    _TEST_INSUREE_CHFID_NOT_EXIST = "NotExistedCHF"

    _test_json_path_credentials = "/test/test_login.json"
    
    _test_request_data_credentials = None
    _test_request_data = None
    test_village = None
    test_insuree = None
    sub_str={}

    def setUp(self):
        super(GroupAPITests, self).setUp()

        self.get_or_create_user_api()
        self.create_dependencies()

        self.sub_str[self._TEST_INSUREE_CHFID] = self.test_insuree.chf_id
        self.sub_str[self._TEST_INSUREE_UUID] = self.test_insuree.uuid

        
        self._test_request_data = load_and_replace_json(self._test_json_path,self.sub_str)

    def verify_updated_obj(self, updated_obj):
        self.assertTrue(isinstance(updated_obj, Group))
        poverty_data = None
        for extension in updated_obj.extension:
            if "group-poverty-status" in extension.url:
                poverty_data = extension
        self.assertEqual(self._TEST_POVERTY_STATUS, poverty_data.valueBoolean)

    def update_resource(self, data):
        for extension in data["extension"]:
            if "group-poverty-status" in extension["url"]:
                extension["valueBoolean"] = self._TEST_POVERTY_STATUS

    def create_dependencies(self):
        self.test_insuree = create_test_insuree(
            with_family=False,
            custom_props=
            {
                "family_id": None,
                "last_name": self._TEST_INSUREE_LAST_NAME,
                "other_names": self._TEST_INSUREE_OTHER_NAMES,
            }
        )
        self.test_village = self.test_insuree.current_village
    def update_payload_no_extensions(self, data):
        data["extension"] = []
        return data

    def update_payload_no_such_chf_id(self, data):
        for member in data["member"]:
            member["entity"]["reference"] = f"Patient/{self._TEST_INSUREE_CHFID_NOT_EXIST}"
        return data

    def update_payload_remove_chf_id_from_it(self, data):
        for member in data["member"]:
            member["entity"].pop("reference")
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
        #FIXME location reference not used self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        #self.assertIsNotNone(response.content)

    def test_post_should_raise_error_no_extensions(self):
        self.login()
        self.create_dependencies()
        modified_payload = self.update_payload_no_extensions(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        response_json = response.json()
        self.assertEqual(
            self.get_response_details(response_json),
            _("At least one extension with address is required")
        )

    def test_post_should_raise_error_no_such_chf_id(self):
        self.login()
        self.create_dependencies()
        modified_payload = self.update_payload_no_such_chf_id(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')
        self.assertTrue(status.is_server_error(response.status_code))

        response_json = response.json()
        self.assertIsNotNone(self.get_response_details(response_json))

    def test_post_should_raise_error_no_chf_id_in_payload(self):
        self.login()
        self.create_dependencies()
        modified_payload = self.update_payload_remove_chf_id_from_it(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json')

        self.assertTrue(status.is_server_error(response.status_code))

        response_json = response.json()
        self.assertIsNotNone(self.get_response_details(response_json))
