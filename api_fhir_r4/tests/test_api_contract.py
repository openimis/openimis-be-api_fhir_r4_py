import json
import os

from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from api_fhir_r4.utils import DbManagerUtils
from rest_framework.test import APITestCase
from rest_framework import status
from core.models import User
from core.services import create_or_update_interactive_user, create_or_update_core_user
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.configurations import GeneralConfiguration
from core.test_helpers import create_test_officer
from insuree.test_helpers import create_test_insuree
from product.test_helpers import create_test_product


class ContractAPITests(GenericFhirAPITestMixin, APITestCase, LogInMixin):

    base_url = GeneralConfiguration.get_base_url()+'Contract/'
    _test_json_path = "/test/test_contract.json"

    _TEST_FAMILY_UUID = "e8bbb7e4-19ef-4bef-9342-9ab6b9a928d3"
    _TEST_OFFICER_UUID = "ff7db42d-874b-400a-bba7-e59b273ae123"
    _TEST_INSUREE_UUID = "f8c56ada-d76d-4f6c-aad3-cfddc9fb38eb"
    _TEST_PRODUCT_CODE = "TE123"
    _TEST_PRODUCT_UUID = "8ed8d2d9-2644-4d29-ba37-ab772386cfca"

    _test_json_path_credentials = "/tests/test/test_login.json"
    _test_request_data_credentials = None

    def setUp(self):
        super(ContractAPITests, self).setUp()
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        json_representation = open(dir_path + self._test_json_path_credentials).read()
        self._test_request_data_credentials = json.loads(json_representation)
        self.get_or_create_user_api()

    def create_dependencies(self):
        # create mocked insuree
        imis_insuree = create_test_insuree(with_family=True)
        imis_insuree.uuid = self._TEST_INSUREE_UUID
        imis_insuree.save()

        # update family uuid
        imis_family = imis_insuree.family
        imis_family.uuid = self._TEST_FAMILY_UUID
        imis_family.save()

        # create mocked product
        imis_product = create_test_product(self._TEST_PRODUCT_CODE, valid=True, custom_props=None)
        imis_product.uuid = self._TEST_PRODUCT_UUID
        imis_product.save()

        # create mocked officer
        imis_officer = create_test_officer()
        imis_officer.uuid = self._TEST_OFFICER_UUID
        imis_officer.save()

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
