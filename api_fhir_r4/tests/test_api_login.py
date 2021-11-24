import json
import os

from core.models import User
from core.services import create_or_update_interactive_user, create_or_update_core_user

from rest_framework import status
from rest_framework.test import APITestCase
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiCreateTestMixin
from api_fhir_r4.utils import DbManagerUtils


class LoginAPITests(GenericFhirAPITestMixin, FhirApiCreateTestMixin, APITestCase):

    base_url = '/api_fhir_r4/login/'
    _test_json_path = "/test/test_login.json"
    _test_json_path_wrong_credentials = "/tests/test/test_login_bad_credentials.json"
    _test_json_path_wrong_payload = "/tests/test/test_login_bad_payload.json"
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
    _test_request_data_wrong_credentials = None
    _test_request_data_bad_payload = None

    def setUp(self):
        super(LoginAPITests, self).setUp()
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        json_representation = open(dir_path + self._test_json_path_wrong_credentials).read()
        self._test_request_data_wrong_credentials = json.loads(json_representation)
        json_representation = open(dir_path + self._test_json_path_wrong_payload).read()
        self._test_request_data_bad_payload = json.loads(json_representation)

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

    def test_post_should_create_correctly(self):
        self.get_or_create_user_api()
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
