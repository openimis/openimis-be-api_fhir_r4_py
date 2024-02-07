import json
import os

from django.db.models import Model
from rest_framework.test import APITestCase
from rest_framework import status
from typing import Type

from core.models import User,filter_validity
from core.services import create_or_update_interactive_user, create_or_update_core_user
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import LocationTestMixin, ClaimAdminPractitionerTestMixin
from api_fhir_r4.utils import DbManagerUtils, TimeUtils
from claim.models import Claim, ClaimAdmin
from location.models import HealthFacility, UserDistrict
from medical.models import Diagnosis, Item, Service
from location.test_helpers import create_test_location, create_test_health_facility, create_test_village
from api_fhir_r4.tests.utils import load_and_replace_json,get_connection_payload,get_or_create_user_api
from medical.test_helpers import create_test_item, create_test_service
from insuree.test_helpers import create_test_insuree
from claim.test_helpers import create_test_claim_admin

from insuree.models import Insuree, Family


class ClaimAPIContainedTestBaseMixin:
    base_url = GeneralConfiguration.get_base_url() + 'Claim/'
    _test_json_request_path = "/test/test_claim_contained.json"

    # diagnosis data
    _TEST_MAIN_ICD_CODE = 'T_CD'
    _TEST_MAIN_ICD_NAME = 'Test diagnosis'

    _TEST_CLAIM_ADMIN_UUID = "044c33d1-dbf3-4d6a-9924-3797b461e535"
    _TEST_INSUREE_UUID = "AAAA08B5-6E85-470C-83EC-0EE9370F0000"
    _TEST_INSUREE_CODE = "105000003"
    _TEST_GROUP_UUID = 'AAAA5232-9054-4D86-B4F2-0E9C4ADF0000'

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
    _TEST_HF_UUID = 'AAAA5F9B-97C6-444B-AAD9-2FCCFD460000'
    _TEST_HF_CODE = "12345678"
    _TEST_HF_NAME = "TEST_NAME"
    _TEST_HF_LEVEL = "H"
    _TEST_HF_LEGAL_FORM = "G"
    _TEST_ADDRESS = "TEST_ADDRESS"
    _TEST_PHONE = "133-996-476"
    _TEST_FAX = "1-408-999 8888"
    _TEST_EMAIL = "TEST@TEST.com"

    _ADMIN_AUDIT_USER_ID = -1

    _test_json_path_credentials = "/test/test_login.json"
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
    test_village = None
    test_hf = None
    test_claim_admin = None
    test_insuree = None
    sub_str = {}

    def setUp(self):
        super(ClaimAPIContainedTestBaseMixin, self).setUp()
        self.create_dependencies()
        self.sub_str[self._TEST_GROUP_UUID] = self.test_insuree.family.uuid
        self.sub_str[self._TEST_INSUREE_UUID] = self.test_insuree.uuid
        self.sub_str[self._TEST_INSUREE_CODE] = self.test_insuree.chf_id
        self.sub_str[self._TEST_CLAIM_ADMIN_UUID] = self.test_claim_admin.uuid
        self.sub_str[self._TEST_HF_UUID] = self.test_hf.uuid
        self.sub_str[self._TEST_HF_CODE] = self.test_hf.code
        
        self._test_request_data = load_and_replace_json(self._test_json_request_path,self.sub_str)
        
        


    def create_dependencies(self):
        self._TEST_USER = get_or_create_user_api(self._TEST_DATA_USER)
        if not  self.test_insuree:
            self.test_insuree = create_test_insuree()
        UserDistrict.objects.create(
            **{
                'user':self._TEST_USER._u,
                'location': self.test_insuree.family.location.parent.parent,
                'audit_user_id':-1
            }
        )
        self.test_icd = Diagnosis()
        self.test_icd.code = self._TEST_MAIN_ICD_CODE
        self.test_icd.name = self._TEST_MAIN_ICD_NAME
        self.test_icd.audit_user_id = self._ADMIN_AUDIT_USER_ID
        self.test_icd.save()


        self.test_village = self.test_insuree.current_village or self.test_insuree.family.location
        self.test_hf=self.create_test_hf()
        self._TEST_HF_ID = self.test_hf.id
        if not self.test_claim_admin:
            self.test_claim_admin =create_test_claim_admin(
                custom_props={'health_facility_id': self.test_hf.id,
                                'last_name' : self._TEST_DATA_USER['last_name'],
                                'other_names' : self._TEST_DATA_USER['other_names']})
        

        ud = UserDistrict()
        ud.location = self.test_village.parent.parent
        ud.audit_user_id = self._ADMIN_AUDIT_USER_ID
        ud.user = self._TEST_USER.i_user
        ud.validity_from = TimeUtils.now()
        ud.save()
        
        self._TEST_USER.claim_admin = self.test_claim_admin
        self._TEST_USER.save()
  

    def create_test_claim_item(self):
        item = create_test_item(
            self._TEST_ITEM_TYPE,
            custom_props={"code": self._TEST_ITEM_CODE}
        )
        item.code = self._TEST_ITEM_CODE
        item.save()
        return item

    def create_test_claim_service(self):
        service = create_test_service(
            self._TEST_SERVICE_TYPE,
            custom_props={"code": self._TEST_SERVICE_CODE}
        )
        service.code = self._TEST_SERVICE_CODE
        service.save()
        return service

    def create_test_hf(self):
        hf = create_test_health_facility(
            self._TEST_HF_CODE,
            self.test_village.parent.parent.id,
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
        return hf

    def assert_response(self, response_json):
        self.assertEqual(response_json["outcome"], 'complete')
        for item in response_json["item"]:
            for adjudication in item["adjudication"]:
                self.assertEqual(adjudication["category"]["coding"][0]["code"], f'{Claim.STATUS_REJECTED}')
                # 2 not in price list
                #FIXME familly in some cases self.assertEqual(adjudication["reason"]["coding"][0]["code"], '2')

        self.assertEqual(response_json["resourceType"], "ClaimResponse")

    def assert_hf_created(self):
        self._assert_unique_created(self.test_hf.uuid, HealthFacility)

    def assert_insuree_created(self):
        insuree = self._assert_unique_created(str(self.test_insuree.uuid), Insuree)

        family = self._assert_unique_created(str(self.test_insuree.family.uuid), Family)

        self.assertEqual(insuree, family.head_insuree)

    def assert_claim_admin_created(self):
        return None#FIXME
        expected_claim_admin_uuid = 'AAAA5229-DD11-4383-863C-E2FAD1B20000'
        self._assert_unique_created(expected_claim_admin_uuid, ClaimAdmin)
        # HF added using practitioner role
        admin = ClaimAdmin.objects.get(uuid=expected_claim_admin_uuid)
        hf = admin.health_facility
        self.assertEqual(hf.uuid, 'AAAA5F9B-97C6-444B-AAD9-2FCCFD460000')

    def assert_items_created(self):
        expected_item_uuid = 'AAAA76E2-DC28-4B48-8E29-3AC4ABEC0000'
        self._assert_unique_created(expected_item_uuid, Item)

        expected_service_uuid = 'AAAA29BA-3F4E-4E6F-B55C-23A488A10000'
        self._assert_unique_created(expected_service_uuid, Service)

    def _assert_unique_created(self, expected_uuid, django_model: Type[Model]):
        msg = f'Contained resource should create unique object of type ' \
              f'{django_model} with uuid {expected_uuid}'

        query = django_model.objects.filter(uuid=expected_uuid).all()

        self.assertEqual(query.count(), 1, msg)
        return query.get()

    def assert_hf_updated(self):
        return None#FIXME
        expected_updated_address = 'Uitly road 1'
        hf = HealthFacility.objects.get(uuid=self.test_hf.uuid)
        self.assertEqual(hf.address, expected_updated_address)

    def assert_contained(self, json_response):
        contained = json_response['contained']
        self.assertResourceExists(contained, 'Patient', 'AAAA08B5-6E85-470C-83EC-0EE9370F0000')
        self.assertResourceExists(contained, 'Organization', 'AAAA5F9B-97C6-444B-AAD9-2FCCFD460000')
        self.assertResourceExists(contained, 'Group', 'AAAA5232-9054-4D86-B4F2-0E9C4ADF0000')
        self.assertResourceExists(contained, 'Practitioner', 'AAAA5229-DD11-4383-863C-E2FAD1B20000')
        self.assertResourceExists(contained, 'Medication', 'AAAA76E2-DC28-4B48-8E29-3AC4ABEC0000')
        self.assertResourceExists(contained, 'ActivityDefinition', 'AAAA29BA-3F4E-4E6F-B55C-23A488A10000')

    def assertResourceExists(self, contained, resource_type, resource_id):
        x = [x for x in contained if x['resourceType'] == resource_type and x['id'] == resource_id]
        self.assertEqual(len(x), 1)


class ClaimAPIContainedTests(ClaimAPIContainedTestBaseMixin, GenericFhirAPITestMixin, APITestCase):
    base_url = GeneralConfiguration.get_base_url() + 'Claim/'
    _test_json_path = "/test/test_claim_contained.json"

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
        response = self.client.post(self.base_url, data=self._test_request_data, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.content)
        response_json = response.json()
        self.assert_response(response_json)
        self.assert_hf_created()
        self.assert_insuree_created()
        self.assert_claim_admin_created()
        #self.assert_items_created()

    def test_post_should_update_contained_correctly(self):
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


        # Confirm HF already exists
        self.assertTrue(HealthFacility.objects.filter(uuid=self.test_hf.uuid).exists())

        response = self.client.post(self.base_url, data=self._test_request_data, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.content)
        response_json = response.json()
        self.assert_response(response_json)
        self.assert_hf_created()
        self.assert_insuree_created()
        self.assert_claim_admin_created()
        #self.assert_items_created()
        self.assert_hf_updated()

    def test_get_should_return_200_claim_with_contained(self):
        # Test if get Claim return contained resources
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
        # Create claim
        response = self.client.post(self.base_url, data=self._test_request_data, format='json', **headers)
        response_json = response.json()
        self.assertTrue(status.is_success(response.status_code))
        uuid = response_json['id']
        url = F"{GeneralConfiguration.get_base_url()}Claim/{uuid}/?contained=True"
        response = self.client.get(url, data=None, format='json', **headers)
        #FIXME replace fix UUID with codes self.assert_contained(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
