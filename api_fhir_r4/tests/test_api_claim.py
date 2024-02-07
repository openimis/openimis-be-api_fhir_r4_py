import json
import os

from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.tests import LocationTestMixin, ClaimAdminPractitionerTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from api_fhir_r4.utils import TimeUtils
from api_fhir_r4.tests.utils import load_and_replace_json,get_connection_payload,get_or_create_user_api
from api_fhir_r4.utils import DbManagerUtils

from claim.models import Claim, ClaimDetail
from insuree.test_helpers import create_test_insuree
from location.models import HealthFacility, UserDistrict
from location.test_helpers import create_test_village, create_test_health_facility
from medical.models import Diagnosis
from medical.test_helpers import create_test_item, create_test_service
from claim.test_helpers import create_test_claimservice,create_test_claimitem,create_test_claim_admin

class ClaimAPITests(GenericFhirAPITestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url() + 'Claim/'
    _test_json_path = "/test/test_claim.json"

    # diagnosis data
    _TEST_MAIN_ICD_CODE = 'T_CD'
    _TEST_MAIN_ICD_NAME = 'Test diagnosis'

    _TEST_CLAIM_ADMIN_UUID = "044c33d1-dbf3-4d6a-9924-3797b461e535"
    _TEST_CLAIM_ADMIN_CODE = "VITEST99"
    _TEST_INSUREE_CODE = "999000001"
    _TEST_INSUREE_UUID = '76aca309-f8cf-4890-8f2e-b416d78de00b'
    # claim item data
    _TEST_ITEM_CODE = "0004"
    _TEST_ITEM_UUID = "e2bc1546-390b-4d41-8571-632ecf7a0936"
    _TEST_ITEM_QUANTITY_PROVIDED = 10.0
    _TEST_ITEM_PRICE_ASKED = 10.0
    _TEST_ITEM_EXPLANATION = "item_explanation"
    _TEST_ITEM_TYPE = 'D'

    # claim service data
    _TEST_SERVICE_CODE = "M7"
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
    _TEST_USER = None
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

    _test_json_path_credentials = "/test/test_login.json"
    _test_request_data_credentials = None
    _test_json_path_with_code_references = "/test/test_claim_with_code_references.json"
    sub_str = {}
    test_insuree = None
    test_claim_admin = None
 
    def setUp(self):
        super(ClaimAPITests, self).setUp()
        self._TEST_USER = get_or_create_user_api(self._TEST_DATA_USER)
        self.create_dependencies()
        self.sub_str[self._TEST_INSUREE_UUID]=self.test_insuree.uuid
        self.sub_str[self._TEST_INSUREE_CODE]=self.test_insuree.chf_id
        self.sub_str[self._TEST_HF_UUID]=self.test_hf.uuid
        self.sub_str[self._TEST_CLAIM_ADMIN_UUID]=self.test_claim_admin.uuid
        self.sub_str[self._TEST_CLAIM_ADMIN_CODE]=self.test_claim_admin.code

        self.sub_str[self._TEST_ITEM_UUID]=self._TEST_ITEM.uuid
        self.sub_str[self._TEST_SERVICE_UUID]=self._TEST_SERVICE.uuid
        self.sub_str[self._TEST_ITEM_CODE]=self._TEST_ITEM.code
        self.sub_str[self._TEST_SERVICE_CODE]=self._TEST_SERVICE.code
        self._TEST_HF_ID = self.test_hf.id
        self._TEST_HF_UUID = self.test_hf.uuid



    def create_dependencies(self):
        self.test_icd = Diagnosis(code=self._TEST_MAIN_ICD_CODE, name =self._TEST_MAIN_ICD_NAME)
        self.test_icd.audit_user_id = self._ADMIN_AUDIT_USER_ID
        self.test_icd.save()
        self.test_insuree = create_test_insuree(custom_props={"chf_id": self._TEST_INSUREE_CODE})
        self.test_hf = self.create_test_hf()
        if not self.test_claim_admin:
            self.test_claim_admin =create_test_claim_admin(
                custom_props={'code':'T-CA-API',
                              'health_facility_id': self.test_hf.id,
                                'last_name' : self._TEST_DATA_USER['last_name'],
                                'other_names' : self._TEST_DATA_USER['other_names']})
        
        self._TEST_USER.claim_admin = self.test_claim_admin
        self._TEST_USER.save()
        ud = UserDistrict()
        ud.location = self.test_insuree.family.location.parent.parent
        ud.audit_user_id = self._ADMIN_AUDIT_USER_ID
        ud.user = self._TEST_USER.i_user
        ud.validity_from = TimeUtils.now()
        ud.save()

        self._TEST_ITEM = create_test_item(self._TEST_SERVICE_TYPE)
        self._TEST_SERVICE = create_test_service(self._TEST_ITEM_TYPE)

    def create_test_hf(self):
        self.test_hf = create_test_health_facility(
            self._TEST_HF_CODE,
            self.test_insuree.family.location.parent.parent.id,
            custom_props = {
                'name': self._TEST_HF_NAME,
                'level':self._TEST_HF_LEVEL,
                'legal_form_id':self._TEST_HF_LEGAL_FORM,
                'address':self._TEST_ADDRESS,
                'phone':self._TEST_PHONE,
                'fax':self._TEST_FAX,
                'email':self._TEST_EMAIL,
            }
        )
        return self.test_hf



    def _post_claim(self, data, headers):
        return self.client.post(self.base_url, data=data, format='json', **headers)


    def test_post_should_create_correctly(self):
        response = self.client.post(
            GeneralConfiguration.get_base_url() + 'login/', data=get_connection_payload(self._TEST_DATA_USER), format='json'
        )
        response_json = response.json()
        token = response_json["token"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            "Content-Type": "application/json",
            "HTTP_AUTHORIZATION": f"Bearer {token}"
        }

        dataset = [
            load_and_replace_json(self._test_json_path,self.sub_str),
            load_and_replace_json(self._test_json_path_with_code_references,self.sub_str)
        ]
        for data in dataset:
            response = self.client.post(self.base_url, data=data, format='json', **headers)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
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


    def test_get_should_return_200_claim_response(self):
        # test if get ClaimResponse return 200
        response = self.client.post(
            GeneralConfiguration.get_base_url() + 'login/', data=get_connection_payload(self._TEST_DATA_USER), format='json'
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
