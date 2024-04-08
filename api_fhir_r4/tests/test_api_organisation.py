from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiReadTestMixin
from rest_framework.test import APITestCase
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from graphql_jwt.shortcuts import get_token
from core.test_helpers import create_test_interactive_user
from dataclasses import dataclass
from core.models import User
from rest_framework import status
from policyholder.tests.helpers import create_test_policy_holder

@dataclass
class DummyContext:
    """ Just because we need a context to generate. """
    user: User

class OrganisationAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url() + 'Organization/'
    _test_json_path = None
    _test_request_data_credentials = None
    admin_token = None 
    admin_user = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_policy_holder = create_test_policy_holder()
        cls.admin_user = create_test_interactive_user(username="testLocationAdmin")
        cls.admin_token = get_token(cls.admin_user, DummyContext(user=cls.admin_user))


    def test_simple_list_page_2(self):
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {self.admin_token}"
        }
        response = self.client.get(self.base_url+ '?page-offset=2', format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.content)
    
    def test_simple_ph(self):
        headers = {
            "Content-Type": "application/json",
            'HTTP_AUTHORIZATION': f"Bearer {self.admin_token}"
        }
        #
        response = self.client.get(self.base_url+ str(self.test_policy_holder.uuid).upper()+ '/' , format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.content)        
        
    def get_or_create_user_api(self):
        user = DbManagerUtils.get_object_or_none(User, username=self._TEST_USER_NAME)
        if user is None:
            user = self.__create_user_interactive_core()
        return user
