import json
import os

from django.db.models import Model
from rest_framework.test import APITestCase
from rest_framework import status
from typing import Type

from core.models import User
from core.services import create_or_update_interactive_user, create_or_update_core_user
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import LocationTestMixin, ClaimAdminPractitionerTestMixin
from api_fhir_r4.utils import DbManagerUtils, TimeUtils
from claim.models import Claim, ClaimAdmin
from location.models import HealthFacility, UserDistrict
from medical.models import Diagnosis, Item, Service

from medical.test_helpers import create_test_item, create_test_service

from insuree.models import Insuree, Family


class ClaimAPIContainedTestBaseMixin:
    base_url = GeneralConfiguration.get_base_url() + 'Claim/'
    _test_json_request_path = "/test/test_claim_contained.json"

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

    _test_json_path_credentials = "/tests/test/test_login.json"
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
        super(ClaimAPIContainedTestBaseMixin, self).setUp()
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        json_representation = open(dir_path + self._test_json_path_credentials).read()
        self._test_request_data_credentials = json.loads(json_representation)
        self._TEST_USER = self.get_or_create_user_api()
        self.create_dependencies()

    def get_or_create_user_api(self):
        user = DbManagerUtils.get_object_or_none(User, username=self._TEST_USER_NAME)
        if user is None:
            user = self.__create_user_interactive_core()
        return user

    def __create_user_interactive_core(self):
        i_user, i_user_created = create_or_update_interactive_user(
            user_id=None, data=self._TEST_DATA_USER, audit_user_id=999, connected=False
        )
        create_or_update_core_user(
            user_uuid=None, username=self._TEST_DATA_USER["username"], i_user=i_user
        )
        return DbManagerUtils.get_object_or_none(User, username=self._TEST_USER_NAME)

    def create_dependencies(self):
        self._TEST_DIAGNOSIS_CODE = Diagnosis()
        self._TEST_DIAGNOSIS_CODE.code = self._TEST_MAIN_ICD_CODE
        self._TEST_DIAGNOSIS_CODE.name = self._TEST_MAIN_ICD_NAME
        self._TEST_DIAGNOSIS_CODE.audit_user_id = self._ADMIN_AUDIT_USER_ID
        self._TEST_DIAGNOSIS_CODE.save()

        self._TEST_CLAIM_ADMIN = ClaimAdminPractitionerTestMixin().create_test_imis_instance()
        self._TEST_CLAIM_ADMIN.uuid = self._TEST_CLAIM_ADMIN_UUID
        self._TEST_CLAIM_ADMIN.save()
        self._TEST_LOCATION = self.create_test_location()

    def create_test_location(self):
        location = LocationTestMixin().create_test_imis_instance()
        location.uuid = 'AAAA6B35-30EF-4E42-AB04-46AC043D0000'
        location.save()

        ud = UserDistrict()
        ud.location = location.parent.parent
        ud.audit_user_id = self._ADMIN_AUDIT_USER_ID
        ud.user = self._TEST_USER.i_user
        ud.validity_from = TimeUtils.now()
        ud.save()
        return location

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
        hf = HealthFacility()
        hf.id = self._TEST_HF_ID
        hf.uuid = 'AAAA5F9B-97C6-444B-AAD9-2FCCFD460000'
        hf.code = self._TEST_HF_CODE
        hf.name = self._TEST_HF_NAME
        hf.level = self._TEST_HF_LEVEL
        hf.legal_form_id = self._TEST_HF_LEGAL_FORM
        hf.address = self._TEST_ADDRESS
        hf.phone = self._TEST_PHONE
        hf.fax = self._TEST_FAX
        hf.email = self._TEST_EMAIL
        hf.location_id = self._TEST_LOCATION.parent.parent.id
        hf.offline = False
        hf.audit_user_id = self._ADMIN_AUDIT_USER_ID
        hf.save()
        return hf

    def assert_response(self, response_json):
        self.assertEqual(response_json["outcome"], 'complete')
        for item in response_json["item"]:
            for adjudication in item["adjudication"]:
                self.assertEqual(adjudication["category"]["coding"][0]["code"], f'{Claim.STATUS_REJECTED}')
                # 2 not in price list
                self.assertEqual(adjudication["reason"]["coding"][0]["code"], '2')

        self.assertEqual(response_json["resourceType"], "ClaimResponse")

    def assert_hf_created(self):
        expected_hf_uuid = 'AAAA5F9B-97C6-444B-AAD9-2FCCFD460000'
        self._assert_unique_created(expected_hf_uuid, HealthFacility)

    def assert_insuree_created(self):
        expected_insuree_uuid = 'AAAA08B5-6E85-470C-83EC-0EE9370F0000'
        insuree = self._assert_unique_created(expected_insuree_uuid, Insuree)

        expected_family_uuid = 'AAAA5232-9054-4D86-B4F2-0E9C4ADF0000'
        family = self._assert_unique_created(expected_family_uuid, Family)

        self.assertEqual(insuree, family.head_insuree)

    def assert_claim_admin_created(self):
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
        expected_updated_address = 'Uitly road 1'
        hf = HealthFacility.objects.get(uuid='AAAA5F9B-97C6-444B-AAD9-2FCCFD460000')
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
        self.assert_response(response_json)
        self.assert_hf_created()
        self.assert_insuree_created()
        self.assert_claim_admin_created()
        self.assert_items_created()

    def test_post_should_update_contained_correctly(self):
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

        self.create_test_hf()
        # Confirm HF already exists
        self.assertTrue(HealthFacility.objects.filter(uuid=self._TEST_HF_UUID).exists())

        response = self.client.post(self.base_url, data=self._test_request_data, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.content)
        response_json = response.json()
        self.assert_response(response_json)
        self.assert_hf_created()
        self.assert_insuree_created()
        self.assert_claim_admin_created()
        self.assert_items_created()
        self.assert_hf_updated()

    def test_get_should_return_200_claim_with_contained(self):
        # Test if get Claim return contained resources
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
        # Create claim
        response = self.client.post(self.base_url, data=self._test_request_data, format='json', **headers)
        response_json = response.json()
        self.assertTrue(status.is_success(response.status_code))
        uuid = response_json['id']
        url = F"{GeneralConfiguration.get_base_url()}Claim/{uuid}/?contained=True"
        response = self.client.get(url, data=None, format='json', **headers)
        self.assert_contained(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
