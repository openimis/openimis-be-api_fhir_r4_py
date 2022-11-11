from rest_framework import status
from rest_framework.test import APITestCase
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.configurations import GeneralConfiguration
from insuree.models import FamilyType


class CodeSystemGroupTypeAPITests(GenericFhirAPITestMixin, APITestCase):
    base_url = GeneralConfiguration.get_base_url() + 'CodeSystem/group-type/'

    def setUp(self):
        super(CodeSystemGroupTypeAPITests, self).setUp()
        self._EXPECTED_COUNT = FamilyType.objects.all().count()

    def test_get_bad_authorization(self):
        response = self.client.get(self.base_url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_should_return_code_system(self):
        self.login()
        response = self.client.get(self.base_url, data=None, format='json')
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['count'], self._EXPECTED_COUNT)
        self.assertEqual(response_data['name'], 'GroupTypeCS')
        self.assertEqual(response_data['title'], 'Group Type (Group)')
