import json
import os

from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.tests import LocationTestMixin, ClaimAdminPractitionerTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from api_fhir_r4.utils import TimeUtils
from claim.models import Claim
from insuree.test_helpers import create_test_insuree
from location.models import HealthFacility, UserDistrict
from medical.models import Diagnosis
from medical.test_helpers import create_test_item, create_test_service


class ClaimAPITests(GenericFhirAPITestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url() + 'Claim/'
    _test_json_path = "/test/test_claim.json"

    # diagnosis data
    _TEST_MAIN_ICD_CODE = 'T_CD'
    _TEST_MAIN_ICD_NAME = 'Test diagnosis'

    _TEST_CLAIM_ADMIN_UUID = "044c33d1-dbf3-4d6a-9924-3797b461e535"
    _TEST_INSUREE_UUID = "76aca309-f8cf-4890-8f2e-b416d78de00b"

    # claim item data
    _TEST_ITEM_CODE = "iCode"
    _TEST_ITEM_UUID = "e2bc1546-390b-4d41-8571-632ecf7a0936"
    _TEST_ITEM_QUANTITY_PROVIDED = 10.0
    _TEST_ITEM_PRICE_ASKED = 10.0
    _TEST_ITEM_EXPLANATION = "item_explanation"
    _TEST_ITEM_TYPE = 'D'

    # claim service data
    _TEST_SERVICE_CODE = "sCode"
    _TEST_SERVICE_UUID = "a17602f4-e9ff-4f42-a6a4-ccefcb23b4d6"
    _TEST_SERVICE_QUANTITY_PROVIDED = 1
    _TEST_SERVICE_PRICE_ASKED = 21000.0
    _TEST_SERVICE_EXPLANATION = "service_explanation"
    _TEST_SERVICE_TYPE = 'D'

    # hf test data
    _TEST_HF_ID = 10000
    _TEST_HF_UUID = "6d0eea8c-62eb-11ea-94d6-c36229a16c2f"
    _TEST_HF_CODE = "12345678"
    _TEST_HF_NAME = "TEST_NAME"
    _TEST_HF_LEVEL = "H"
    _TEST_HF_LEGAL_FORM = "G"
    _TEST_ADDRESS = "TEST_ADDRESS"
    _TEST_PHONE = "133-996-476"
    _TEST_FAX = "1-408-999 8888"
    _TEST_EMAIL = "TEST@TEST.com"

    _ADMIN_AUDIT_USER_ID = -1

    _test_json_path_credentials = "/tests/test/test_login.json"
    _test_request_data_credentials = None

    def setUp(self):
        super(ClaimAPITests, self).setUp()
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        json_representation = open(dir_path + self._test_json_path_credentials).read()
        self._test_request_data_credentials = json.loads(json_representation)
        self._TEST_USER = self.get_or_create_user_api()
        self.create_dependencies()

    def create_dependencies(self):
        self._TEST_DIAGNOSIS_CODE = Diagnosis()
        self._TEST_DIAGNOSIS_CODE.code = self._TEST_MAIN_ICD_CODE
        self._TEST_DIAGNOSIS_CODE.name = self._TEST_MAIN_ICD_NAME
        self._TEST_DIAGNOSIS_CODE.audit_user_id = self._ADMIN_AUDIT_USER_ID
        self._TEST_DIAGNOSIS_CODE.save()

        self._TEST_CLAIM_ADMIN = ClaimAdminPractitionerTestMixin().create_test_imis_instance()
        self._TEST_CLAIM_ADMIN.uuid = self._TEST_CLAIM_ADMIN_UUID
        self._TEST_CLAIM_ADMIN.save()
        self._TEST_HF = self.create_test_health_facility()

        self._TEST_INSUREE = create_test_insuree()
        self._TEST_INSUREE.uuid = self._TEST_INSUREE_UUID
        self._TEST_INSUREE.save()
        self._TEST_ITEM = self.create_test_claim_item()
        self._TEST_SERVICE = self.create_test_claim_service()

    def create_test_health_facility(self):
        location = LocationTestMixin().create_test_imis_instance()
        location.save()
        hf = HealthFacility()
        hf.id = self._TEST_HF_ID
        hf.uuid = self._TEST_HF_UUID
        hf.code = self._TEST_HF_CODE
        hf.name = self._TEST_HF_NAME
        hf.level = self._TEST_HF_LEVEL
        hf.legal_form_id = self._TEST_HF_LEGAL_FORM
        hf.address = self._TEST_ADDRESS
        hf.phone = self._TEST_PHONE
        hf.fax = self._TEST_FAX
        hf.email = self._TEST_EMAIL
        hf.location_id = location.id
        hf.offline = False
        hf.audit_user_id = self._ADMIN_AUDIT_USER_ID
        hf.save()
        ud = UserDistrict()
        ud.location = location
        ud.audit_user_id = self._ADMIN_AUDIT_USER_ID
        ud.user = self._TEST_USER.i_user
        ud.validity_from = TimeUtils.now()
        ud.save()
        return hf

    def create_test_claim_item(self):
        item = create_test_item(
            self._TEST_ITEM_TYPE,
            custom_props={"code": self._TEST_ITEM_CODE}
        )
        item.code = self._TEST_ITEM_CODE
        item.uuid = self._TEST_ITEM_UUID
        item.save()
        return item

    def create_test_claim_service(self):
        service = create_test_service(
            self._TEST_SERVICE_TYPE,
            custom_props={"code": self._TEST_SERVICE_CODE}
        )
        service.code = self._TEST_SERVICE_CODE
        service.uuid = self._TEST_SERVICE_UUID
        service.save()
        return service

    def test_post_should_create_correctly(self):
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
        response = self.client.post(self.base_url, data=self._test_request_data, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.content)
        response_json = response.json()
        self.assertEqual(response_json["resourceType"], 'ClaimResponse')
        self.assertEqual(response_json["outcome"], 'complete')
        # for both tests item and service should be 'rejected' and 'not in price list'
        for item in response_json["item"]:
            for adjudication in item["adjudication"]:
                self.assertEqual(adjudication["category"]["coding"][0]["code"], f'{Claim.STATUS_REJECTED}')
                # 2 not in price list
                self.assertEqual(adjudication["reason"]["coding"][0]["code"], '2')

        self.assertEqual(response_json["resourceType"], "ClaimResponse")

    def test_get_should_return_200_claim_response(self):
        # test if get ClaimResponse return 200
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
        response = self.client.get(GeneralConfiguration.get_base_url() + 'ClaimResponse/', data=None, format='json',
                                   **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
