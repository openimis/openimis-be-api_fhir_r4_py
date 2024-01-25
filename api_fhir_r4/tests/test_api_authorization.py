import json
import os

from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin
from gettext import gettext as _

from api_fhir_r4.tests.utils import get_connection_payload,get_or_create_user_api

class AuthorizationAPITests(GenericFhirAPITestMixin, APITestCase):
    base_url = GeneralConfiguration.get_base_url()
    url_to_test_authorization = base_url + 'Group/'
    _test_json_path = "/test/test_login.json"
    _test_json_path_credentials = "/test/test_login.json"
    _test_request_data_credentials = None

    def setUp(self):
        super(AuthorizationAPITests, self).setUp()
        self.test_user = get_or_create_user_api()

    def get_bundle_from_json_response(self, response):
        pass

    def test_post_should_authorize_correctly(self):
        response = self.client.post(self.base_url + 'login/', data=get_connection_payload(), format='json')
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
        self.assertEqual(self.get_response_details(response_json), "Authentication credentials were not provided.")

    def test_post_should_raise_error_decode_token(self):
        response = self.client.post(self.base_url + 'login/', data=get_connection_payload(), format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token}ssdd"
        }
        response = self.client.get(self.url_to_test_authorization, format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.get_response_details(response_json), _('INCORRECT_CREDENTIALS'))

    def test_post_should_raise_lack_of_bearer_prefix(self):
        response = self.client.post(self.base_url + 'login/', data=get_connection_payload(), format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"{token}"
        }
        response = self.client.get(self.url_to_test_authorization, format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertTrue(self.get_response_details(response_json) != '',
                        msg="401 Response without error message")

    def test_post_should_raise_unproper_structure_of_token(self):
        response = self.client.post(self.base_url + 'login/', data=get_connection_payload(), format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token} xxxxx xxxxxx"
        }
        response = self.client.get(self.url_to_test_authorization, format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(self.get_response_details(response_json) != '',
                        msg="401 Response without error message")

    def test_post_should_raise_forbidden(self):
        response = self.client.post(self.base_url + 'login/', data=get_connection_payload(), format='json')
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
            self.get_response_details(response_json), "User unauthorized for any of the resourceType available in the view."
        )

    def test_get_should_required_login(self):
        pass
