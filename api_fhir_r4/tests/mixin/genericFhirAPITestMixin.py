import json
import os

from core.models import User
from fhir.resources.R4B import construct_fhir_element
from rest_framework import status

from api_fhir_r4.configurations import (
    R4IdentifierConfig,
    GeneralConfiguration
)
from api_fhir_r4.converters import BaseFHIRConverter
from fhir.resources.R4B.bundle import Bundle
from api_fhir_r4.utils import DbManagerUtils


class GenericFhirAPITestMixin(object):

    @property
    def base_url(self):
        return None

    @property
    def _test_json_path(self):
        return None
    
    @property
    def _test_json_path_credentials(self):
        return None
    
    _TEST_SUPERUSER_NAME = 'admin'
    _TEST_SUPERUSER_PASS = 'adminadmin'#'Admin123'
    _test_request_data = None
    _test_json_path_credentials = None

    def setUp(self):
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        if self._test_json_path and  self._test_request_data is None:
            json_representation = open(dir_path + self._test_json_path).read()
            self._test_request_data = json.loads(json_representation)
        if self._test_json_path_credentials and  self._test_request_data_credentials is None:
            json_representation = open(dir_path + self._test_json_path_credentials).read()
            self._test_request_data_credentials = json.loads(json_representation)

    def apply_replace_map(self , payload):
        return payload

    def initialize_auth(self):
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
        return headers
    def get_response_details(self, response_json):
        if 'issue' in response_json\
            and len(response_json["issue"])>0\
            and 'details' in response_json["issue"][0]\
            and 'text' in response_json["issue"][0]["details"]: 
            return response_json["issue"][0]["details"]['text'] 

        
        elif 'detail' in response_json:
            return response_json["detail"]
  
    def login(self):
        user = DbManagerUtils.get_object_or_none(User, username=self._TEST_SUPERUSER_NAME)
        if user is None:
            user = self.__create_superuser()
        self.client.force_authenticate(user=user)

    def __create_superuser(self):
        User.objects.create_superuser(username=self._TEST_SUPERUSER_NAME, password=self._TEST_SUPERUSER_PASS)
        return DbManagerUtils.get_object_or_none(User, username=self._TEST_SUPERUSER_NAME)

    def get_bundle_from_json_response(self, response):
        response_json = response.json()
        bundle = construct_fhir_element(response_json['resourceType'], response_json)
        self.assertTrue(isinstance(bundle, Bundle))
        return bundle

    def get_id_for_created_resource(self, response):
        result = None
        response_json = response.json()
        fhir_obj = construct_fhir_element(response_json['resourceType'], response_json)
        if hasattr(fhir_obj, 'identifier'):
            result = BaseFHIRConverter.get_fhir_identifier_by_code(fhir_obj.identifier,
                                                                   R4IdentifierConfig.get_fhir_uuid_type_code())
        return result

    def get_fhir_obj_from_json_response(self, response):
        fhir_obj = None
        response_json = response.json()
        if 'resourceType' in response_json:
            fhir_obj = construct_fhir_element(response_json['resourceType'], response_json)
            
        return fhir_obj

    def test_get_should_required_login(self):
        response = self.client.get(self.base_url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
