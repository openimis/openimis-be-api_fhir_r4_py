import json
import os

from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin


class CommunicationRequestAPITests(GenericFhirAPITestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url() + 'CommunicationRequest/'
    _test_json_path = "/test/test_communicationRequest.json"

    _test_json_path_credentials = "/test/test_login.json"
    _test_request_data_credentials = None

    def setUp(self):
        super(CommunicationRequestAPITests, self).setUp()
        self._TEST_USER = self.get_or_create_user_api()

    def test_get_should_return_200(self):
        # test if return 200
        response = self.client.post(
            GeneralConfiguration.get_base_url() + 'login/', data=self._test_request_data_credentials, format='json'
        )
        response_json = response.json()
        token = response_json["token"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            "Content-Type": "application/json",
            "HTTP_AUTHORIZATION": f"Bearer {token}"
        }
        response = self.client.get(self.base_url, data=None, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
