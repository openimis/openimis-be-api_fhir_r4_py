import json
import os

from core.models import User
from core.services import create_or_update_interactive_user, create_or_update_core_user

from rest_framework import status
from rest_framework.test import APITestCase
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.utils import DbManagerUtils


class AuthorizationAPITests(GenericFhirAPITestMixin, APITestCase):

    base_url = '/api_fhir_r4/login/'
    url_to_test_authorization = '/api_fhir_r4/Group/'
    _test_json_path = "/test/test_login.json"
    _test_json_path_credentials = "/tests/test/test_login.json"
    _TEST_EXPECTED_NAME = "UPDATED_NAME"
    _TEST_USER_NAME = "TestUserTest2"
    _TEST_USER_PASSWORD = "TestPasswordTest2"
    _TEST_DATA_USER = {
        "username": _TEST_USER_NAME,
        "last_name": _TEST_USER_NAME,
        "password": _TEST_USER_PASSWORD,
        "other_names": _TEST_USER_NAME,
        "user_types": "INTERACTIVE",
        "language": "en",
        "roles": [9],
    }
    _test_request_data_credentials = None

    def setUp(self):
        super(AuthorizationAPITests, self).setUp()
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        json_representation = open(dir_path + self._test_json_path_credentials).read()
        self._test_request_data_credentials = json.loads(json_representation)
        self.get_or_create_user_api()

    def get_or_create_user_api(self):
        user = DbManagerUtils.get_object_or_none(User, username=self._TEST_USER_NAME)
        if user is None:
            user = self.__create_user_interactive_core()
        return user

    def get_bundle_from_json_response(self, response):
        pass

    def __create_user_interactive_core(self):
        i_user, i_user_created = create_or_update_interactive_user(
            user_id=None, data=self._TEST_DATA_USER, audit_user_id=999, connected=False)
        create_or_update_core_user(
            user_uuid=None, username=self._TEST_DATA_USER["username"], i_user=i_user)
        return DbManagerUtils.get_object_or_none(User, username=self._TEST_USER_NAME)

    def test_post_should_authorize_correctly(self):
        response = self.client.post(self.base_url, data=self._test_request_data_credentials, format='json')
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
        response = self.client.post(self.base_url, data=self._test_request_data_credentials, format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token}ssdd"
        }
        response = self.client.get(self.url_to_test_authorization, format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response_json["issue"][0]["details"]["text"], "Error on decoding token")

    def test_post_should_raise_lack_of_bearer_prefix(self):
        response = self.client.post(self.base_url, data=self._test_request_data_credentials, format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"{token}"
        }
        response = self.client.get(self.url_to_test_authorization, format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response_json["issue"][0]["details"]["text"], "Missing 'Bearer' prefix")

    def test_post_should_raise_unproper_structure_of_token(self):
        response = self.client.post(self.base_url, data=self._test_request_data_credentials, format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token} xxxxx xxxxxx"
        }
        response = self.client.get(self.url_to_test_authorization, format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response_json["issue"][0]["details"]["text"], "Unproper structure of token")

    def test_post_should_raise_forbidden(self):
        response = self.client.post(self.base_url, data=self._test_request_data_credentials, format='json')
        response_json = response.json()
        token = response_json["token"]
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token}"
        }
        response = self.client.get('/api_fhir_r4/Organisation/', format='json', **headers)
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response_json["issue"][0]["details"]["text"], "You do not have permission to perform this action."
        )

    def test_get_should_required_login(self):
        pass
