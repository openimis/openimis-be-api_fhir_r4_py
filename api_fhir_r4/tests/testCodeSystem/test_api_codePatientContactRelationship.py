from rest_framework import status
from rest_framework.test import APITestCase
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.configurations import GeneralConfiguration
from insuree.models import Relation


class CodeSystemPatientContactRelationshipAPITests(GenericFhirAPITestMixin, APITestCase):

    base_url = GeneralConfiguration.get_base_url()+'CodeSystem/patient-contact-relationship/'

    def setUp(self):
        self._EXPECTED_COUNT = Relation.objects.all().count()

    def test_get_bad_authorization(self):
        response = self.client.get(self.base_url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_should_return_code_system(self):
        self.login()
        response = self.client.get(self.base_url, data=None, format='json')
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        brother_sister = ""
        for concept in response_data['concept']:
            if concept['display'] == 'Brother/Sister':
                brother_sister = concept['display']
        self.assertEqual(brother_sister, 'Brother/Sister')
        self.assertEqual(response_data['count'], self._EXPECTED_COUNT)
        self.assertEqual(response_data['name'], 'PatientContactRelationshipCS')
        self.assertEqual(response_data['title'], 'Contact Relationship (Patient)')
