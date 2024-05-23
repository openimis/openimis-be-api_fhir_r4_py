import json
import os

from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiCreateTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin


class LoginAPITests(GenericFhirAPITestMixin, FhirApiCreateTestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url() + 'login/'
    _test_json_path = "/test/test_login.json"
    _test_json_path_wrong_credentials = "/tests/test/test_login_bad_credentials.json"
    _test_json_path_wrong_payload = "/tests/test/test_login_bad_payload.json"
    _TEST_EXPECTED_NAME = "UPDATED_NAME"
    _test_request_data_wrong_credentials = None
    _test_request_data_bad_payload = None

    def setUp(self):
        super(LoginAPITests, self).setUp()
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        json_representation = open(dir_path + self._test_json_path_wrong_credentials).read()
        self._test_request_data_wrong_credentials = json.loads(json_representation)
        json_representation = open(dir_path + self._test_json_path_wrong_payload).read()
        self._test_request_data_bad_payload = json.loads(json_representation)
        # User
        self.get_or_create_user_api()


    def get_bundle_from_json_response(self, response):
        pass

    def test_post_should_create_correctly(self):
        response = self.client.post(self.base_url, data=self._test_request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_should_give_unathorized(self):
        response = self.client.post(self.base_url, data=self._test_request_data_wrong_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_should_give_bad_request(self):
        response = self.client.post(self.base_url, data=self._test_request_data_bad_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_should_required_login(self):
        pass
