import json
import os

from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin


class AuthorizationAPITests(GenericFhirAPITestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url()
    url_to_test_authorization = base_url + 'Group/'
    _test_json_path = "/test/test_login.json"
    _test_json_path_credentials = "/tests/test/test_login.json"
    _test_request_data_credentials = None

    def setUp(self):
        super(AuthorizationAPITests, self).setUp()
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        json_representation = open(dir_path + self._test_json_path_credentials).read()
        self._test_request_data_credentials = json.loads(json_representation)
        self.get_or_create_user_api()

    def get_bundle_from_json_response(self, response):
        pass

    def test_post_should_authorize_correctly(self):
        response = self.client.post(self.base_url + 'login/', data=self._test_request_data_credentials, format='json')
        response_json = response.json()
        token = response_json["token"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token}"
        }
        response = self.client.get(self.url_to_test_authorization, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_should_raise_no_auth_header(self):
        response = self.client.get(self.url_to_test_authorization, format='json')
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response_json["issue"][0]["details"]["text"], "Authentication credentials were not provided.")

    def test_post_should_raise_error_decode_token(self):
        response = self.client.post(self.base_url + 'login/', data=self._test_request_data_credentials, format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token}ssdd"
        }
        response = self.client.get(self.url_to_test_authorization, format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response_json["issue"][0]["details"]["text"], "Error decoding signature")

    def test_post_should_raise_lack_of_bearer_prefix(self):
        response = self.client.post(self.base_url + 'login/', data=self._test_request_data_credentials, format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"{token}"
        }
        response = self.client.get(self.url_to_test_authorization, format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertTrue(response_json["issue"][0]["details"]["text"] != '',
                        msg="401 Response without error message")

    def test_post_should_raise_unproper_structure_of_token(self):
        response = self.client.post(self.base_url + 'login/', data=self._test_request_data_credentials, format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token} xxxxx xxxxxx"
        }
        response = self.client.get(self.url_to_test_authorization, format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(response_json["issue"][0]["details"]["text"] != '',
                        msg="401 Response without error message")

    def test_post_should_raise_forbidden(self):
        response = self.client.post(self.base_url + 'login/', data=self._test_request_data_credentials, format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token}"
        }
        response = self.client.get(self.base_url + 'Organization/', format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response_json["issue"][0]["details"]["text"], "User unauthorized for any of the resourceType available in the view."
        )

    def test_get_should_required_login(self):
        pass
