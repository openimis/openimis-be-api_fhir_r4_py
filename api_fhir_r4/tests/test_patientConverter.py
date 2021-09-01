import json
import os
from unittest import mock

from api_fhir_r4.converters import PatientConverter

from fhir.resources.patient import Patient
from api_fhir_r4.tests import PatientTestMixin


class PatientConverterTestCase(PatientTestMixin):

    __TEST_PATIENT_JSON_PATH = "/test/test_patient.json"

    def setUp(self):
        super(PatientConverterTestCase, self).setUp()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self._test_patient_json_representation = open(dir_path + self.__TEST_PATIENT_JSON_PATH).read()

    def test_to_fhir_obj(self):
        self.setUp()
        imis_insuree = self.create_test_imis_instance()
        fhir_patient = PatientConverter.to_fhir_obj(imis_insuree)
        self.verify_fhir_instance(fhir_patient)

    @mock.patch('insuree.models.Gender.objects')
    def test_to_imis_obj(self, mock_gender):
        self.setUp()
        mock_gender.get.return_value = self._TEST_GENDER

        fhir_patient = self.create_test_fhir_instance()
        imis_insuree = PatientConverter.to_imis_obj(fhir_patient.dict(), None)
        self.verify_imis_instance(imis_insuree)

    def test_create_object_from_json(self):
        dict_patient = json.loads(self._test_patient_json_representation)
        fhir_patient = Patient(**dict_patient)
        self.verify_fhir_instance(fhir_patient)
