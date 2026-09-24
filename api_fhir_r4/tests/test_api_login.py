import json
import os
import time

from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiCreateTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from core.auth import devices
from core.models import User


def _totp_code(device):
    """A token as the authenticator app would render it, zero-padded."""
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    totp.time = time.time()
    return f"{totp.token():0{device.digits}d}"


class LoginAPITests(
    GenericFhirAPITestMixin, FhirApiCreateTestMixin, APITestCase, LogInMixin
):
    base_url = GeneralConfiguration.get_base_url() + "login/"
    _test_json_path = "/test/test_login.json"
    _test_json_path_wrong_credentials = "/tests/test/test_login_bad_credentials.json"
    _test_json_path_wrong_payload = "/tests/test/test_login_bad_payload.json"
    _TEST_EXPECTED_NAME = "UPDATED_NAME"
    _test_request_data_wrong_credentials = None
    _test_request_data_bad_payload = None

    def setUp(self):
        super(LoginAPITests, self).setUp()
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        json_representation = open(
            dir_path + self._test_json_path_wrong_credentials
        ).read()
        self._test_request_data_wrong_credentials = json.loads(json_representation)
        json_representation = open(dir_path + self._test_json_path_wrong_payload).read()
        self._test_request_data_bad_payload = json.loads(json_representation)
        # User
        self.get_or_create_user_api()

    def get_bundle_from_json_response(self, response):
        pass

    def test_post_should_create_correctly(self):
        response = self.client.post(
            self.base_url, data=self._test_request_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_should_give_unathorized(self):
        response = self.client.post(
            self.base_url, data=self._test_request_data_wrong_credentials, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_should_give_bad_request(self):
        response = self.client.post(
            self.base_url, data=self._test_request_data_bad_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_should_required_login(self):
        pass


class LoginSecondFactorAPITests(GenericFhirAPITestMixin, APITestCase, LogInMixin):
    """The REST login takes the same second factor as tokenAuth: it mints the
    same JWT, so a password alone must not be enough here either."""

    base_url = LoginAPITests.base_url
    _test_json_path = LoginAPITests._test_json_path

    def setUp(self):
        super().setUp()
        self.get_or_create_user_api()

    def test_get_should_required_login(self):
        pass

    def _enrol(self):
        user = User.objects.get(username=self._TEST_USER_NAME)
        device = devices.enrol_totp(user)
        self.assertTrue(devices.confirm_totp(device, _totp_code(device)))
        # Confirming consumes that time step; a real login happens in a later
        # one, so rewind the replay floor rather than wait 30 seconds.
        TOTPDevice.objects.filter(pk=device.pk).update(last_t=-1)
        device.refresh_from_db()
        return device

    def test_post_with_a_device_enrolled_is_told_to_send_a_code(self):
        self._enrol()
        response = self.client.post(
            self.base_url, data=self._test_request_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["detail"], "SECOND_FACTOR_REQUIRED")

    def test_post_with_a_valid_code_logs_in(self):
        device = self._enrol()
        response = self.client.post(
            self.base_url,
            data={**self._test_request_data, "otp": _totp_code(device)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.json())

    def test_post_with_a_wrong_code_is_unauthorized(self):
        self._enrol()
        response = self.client.post(
            self.base_url,
            data={**self._test_request_data, "otp": "000000"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["detail"], "INVALID_SECOND_FACTOR")

    def test_post_while_backing_off_says_when_it_lifts(self):
        self._enrol()
        wrong = {**self._test_request_data, "otp": "000000"}
        self.client.post(self.base_url, data=wrong, format="json")

        response = self.client.post(self.base_url, data=wrong, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["detail"], "SECOND_FACTOR_THROTTLED")
        self.assertTrue(response.json()["locked_until"])
