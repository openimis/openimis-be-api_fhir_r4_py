import json
import os

from core.models import User
from fhir.resources import construct_fhir_element
from rest_framework import status

from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter
from fhir.resources.bundle import Bundle
from api_fhir_r4.utils import DbManagerUtils


class GenericFhirAPITestMixin(object):

    @property
    def base_url(self):
        return None

    @property
    def _test_json_path(self):
        return None

    _TEST_SUPERUSER_NAME = 'admin'
    _TEST_SUPERUSER_PASS = 'adminadmin'#'Admin123'
    _test_request_data = None

    def setUp(self):
        if self._test_json_path:
            dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            json_representation = open(dir_path + self._test_json_path).read()
            self._test_request_data = json.loads(json_representation)

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
        response_json = response.json()
        fhir_obj = construct_fhir_element(response_json['resourceType'], response_json)
        return fhir_obj

    def test_get_should_required_login(self):
        response = self.client.get(self.base_url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
