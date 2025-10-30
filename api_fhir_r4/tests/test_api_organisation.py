import json
import os

from django.utils.translation import gettext as _
from fhir.resources.R4B.organization import Organization
from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiReadTestMixin, LocationTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from policyholder.models import PolicyHolder
from api_fhir_r4.tests.utils import load_and_replace_json


class OrganisationAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url() + 'Organization/'
    _test_json_path = "/test/test_organisation.json"
    _TEST_PH_CODE = "TestPHCode"
    _TEST_PH_NAME = "Test PolicyHolder"

    _test_json_path_credentials = "/test/test_login.json"

    _test_request_data_credentials = None
    _test_request_data = None
    sub_str = {}

    def setUp(self):
        super(OrganisationAPITests, self).setUp()

        self.get_or_create_user_api()
        self.create_dependencies()

        self.sub_str[self._TEST_PH_CODE] = self._TEST_PH_CODE
        self.sub_str[self._TEST_PH_NAME] = self._TEST_PH_NAME

        self._test_request_data = load_and_replace_json(self._test_json_path, self.sub_str)

    def verify_updated_obj(self, updated_obj):
        self.assertTrue(isinstance(updated_obj, Organization))
        self.assertEqual(updated_obj.name, self._TEST_PH_NAME)

    def update_resource(self, data):
        data["name"] = self._TEST_PH_NAME

    def create_dependencies(self):
        pass

    def test_post_should_create_correctly(self):
        self.login()
        response = self.client.post(self.base_url, data=self._test_request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify that a PolicyHolder was created
        ph = PolicyHolder.objects.filter(code=self._TEST_PH_CODE).first()
        self.assertIsNotNone(ph)
        self.assertEqual(ph.trade_name, self._TEST_PH_NAME)

    def test_get_list_should_return_policyholders(self):
        # Create multiple policyholders
        self.login()
        # Create first policyholder
        response1 = self.client.post(self.base_url, data=self._test_request_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Create second policyholder with different data
        sub_str_2 = {
            "TestPHCode": "TestPHCode2",
            "Test PolicyHolder": "Test PolicyHolder 2"
        }
        test_data_2 = load_and_replace_json(self._test_json_path, sub_str_2)
        response2 = self.client.post(self.base_url, data=test_data_2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Get list of policyholders with type=bus
        response = self.client.get(self.base_url + '?type=bus', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response is a Bundle
        bundle = self.get_bundle_from_json_response(response)
        self.assertIsNotNone(bundle.entry)
        self.assertGreaterEqual(len(bundle.entry), 2)

        # Verify the policyholders are in the bundle
        found_ph1 = False
        found_ph2 = False
        for entry in bundle.entry:
            if hasattr(entry.resource, 'name'):
                if entry.resource.name == self._TEST_PH_NAME:
                    found_ph1 = True
                elif entry.resource.name == 'Test PolicyHolder 2':
                    found_ph2 = True

        self.assertTrue(found_ph1, "First policyholder not found in list")
        self.assertTrue(found_ph2, "Second policyholder not found in list")
