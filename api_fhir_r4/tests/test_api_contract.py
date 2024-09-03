import copy
import json
import os

from policy.models import Policy
from rest_framework.status import is_success

from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from api_fhir_r4.utils import DbManagerUtils
from rest_framework.test import APITestCase
from rest_framework import status
from core.models import User
from core.services import create_or_update_interactive_user, create_or_update_core_user
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.tests.utils import load_and_replace_json
from api_fhir_r4.configurations import GeneralConfiguration
from core.test_helpers import create_test_officer
from insuree.models import Insuree
from insuree.test_helpers import create_test_insuree
from product.test_helpers import create_test_product


class ContractAPITests(GenericFhirAPITestMixin, APITestCase, LogInMixin):

    base_url = GeneralConfiguration.get_base_url()+'Contract/'
    _test_json_path = "/test/test_contract.json"

    _TEST_GROUP_UUID = "e8bbb7e4-19ef-4bef-9342-9ab6b9a928d3"
    _TEST_OFFICER_UUID = "ff7db42d-874b-400a-bba7-e59b273ae123"
    _TEST_INSUREE_UUID = "f8c56ada-d76d-4f6c-aad3-cfddc9fb38eb"
    _TEST_PRODUCT_CODE = "TE123"
    _TEST_PRODUCT_UUID = "8ed8d2d9-2644-4d29-ba37-ab772386cfca"

    _test_json_path_credentials = "/test/test_login.json"
    _test_request_data_credentials = None
    test_insuree = None
    test_product = None
    test_officer = None
    sub_str={}
    def setUp(self):
        super(ContractAPITests, self).setUp()
        self.get_or_create_user_api()
# example of use
#        self.sub_str[self._TEST_VILLAGE_UUID] = self.test_village.uuid
#        self.sub_str[self._TEST_SUBSTITUTION_OFFICER_UUID] = self.test_officer.uuid
        self.sub_str[self._TEST_GROUP_UUID] = self.test_insuree.family.uuid
        self.sub_str[self._TEST_INSUREE_UUID] = self.test_insuree.uuid
#        self.sub_str[self._TEST_INSUREE_CHFID] = self.test_insuree.chf_id
        self.sub_str[self._TEST_OFFICER_UUID] = self.test_officer.uuid
#        self.sub_str[self._TEST_CLAIM_ADMIN_UUID] = self.test_claim_admin.uuid
        self.sub_str[self._TEST_PRODUCT_UUID] = self.test_product.uuid
#        
        self._test_request_data = load_and_replace_json(self._test_json_path,self.sub_str)
        
    @classmethod
    def setUpTestData(cls):
        # create mocked insuree
        cls.test_insuree = create_test_insuree(with_family=True)

        # create mocked product
        cls.test_product = create_test_product(cls._TEST_PRODUCT_CODE, valid=True)
   

        # create mocked officer
        cls.test_officer = create_test_officer(custom_props={'uuid':cls._TEST_OFFICER_UUID})


    def test_post_should_create_correctly(self):
        headers = self._build_headers()
        response = self.client.post(self.base_url, data=self._test_request_data, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        self.assertIsNotNone(response.content)

    def test_post_patient_subject_reference(self):
        # Test use case when instead of family, subject is referencing insuree without family
        headers = self._build_headers()

        test_request_data = copy.deepcopy(self._test_request_data)
        #test_request_data['subject'][0]['reference'] = F"Patient/{self.test_insuree.uuid}"
        #test_request_data['author']['reference'] = F"Practitioner/{self.test_officer.uuid}"
        response = self.client.post(self.base_url, data=test_request_data, format='json', **headers)

        self._assert_contract_created(response)
        self._assert_insuree_family_created_in_process(response)

    def _build_headers(self):
        response = self.client.post(
            path=GeneralConfiguration.get_base_url() + 'login/',
            data=self._test_request_data_credentials,
            format='json'
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            f"Login request has failed, bearer token not received, details: {response.json()}")

        token = response.json().get("token")
        return {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {token}"
        }

    def _assert_contract_created(self, response):
        response_status, content = response.status_code, response.json()
        self.assertEqual(
            response_status, status.HTTP_201_CREATED,
            F"Contract POST should return response with code 201, it returned {response_status} instead. \n"
            F"Request details:\n{content}")

        self.assertIsNotNone(
            content,
            "POST Response is marked as success, but response content is empty.")

        policy_id = content['identifier'][0]['value']
        self.assertTrue(
            Policy.objects.filter(uuid__iexact=policy_id, validity_to__isnull=True).exists(),
            "POST Contract returned `201 Created`, but policy object not stored in database")

    def _assert_insuree_family_created_in_process(self, response):
        policy_id = response.json()['identifier'][0]['value']
        policy = Policy.objects.get(uuid=policy_id)
        insuree = Insuree.objects.get(uuid=self.test_insuree.uuid)
        family_policy = policy.family
        family_insuree = insuree.family

        self.assertEqual(
            family_policy, family_insuree,
            F"Contract for insuree reference created but insuree family `{family_insuree}` is "
            F"different from policy family `{family_policy}`.")

        self.assertEqual(
            insuree.current_village, family_policy.location,
            "Family created from insuree object should share location their location.")

        self.assertEqual(family_policy.head_insuree, insuree,
                         "Head of family created from contract is different from contract subject.")

        

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiReadTestMixin
from rest_framework.test import APITestCase
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from graphql_jwt.shortcuts import get_token
from core.test_helpers import create_test_interactive_user
from dataclasses import dataclass
from core.models import User
from rest_framework import status


@dataclass
class DummyContext:
    """ Just because we need a context to generate. """
    user: User

class ContractAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url() + 'Contract/'
    _test_json_path = None
    _test_request_data_credentials = None
    admin_token = None 
    admin_user = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = create_test_interactive_user(username="testLocationAdmin")
        cls.admin_token = get_token(cls.admin_user, DummyContext(user=cls.admin_user))


    def test_simple_list_page_2(self):
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {self.admin_token}"
        }
        response = self.client.get(self.base_url+ '?page-offset=2&page-size=1', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK, json.loads(response.content))
        self.assertIsNotNone(response.content)