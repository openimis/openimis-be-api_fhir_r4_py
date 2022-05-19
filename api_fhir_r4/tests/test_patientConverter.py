from unittest import mock

from api_fhir_r4.converters import PatientConverter

from fhir.resources.patient import Patient
from api_fhir_r4.tests import PatientTestMixin
from api_fhir_r4.tests.mixin import ConvertToFhirTestMixin, ConvertToImisTestMixin, ConvertJsonToFhirTestMixin


class PatientConverterTestCase(PatientTestMixin,
                               ConvertToFhirTestMixin,
                               ConvertToImisTestMixin,
                               ConvertJsonToFhirTestMixin):
    converter = PatientConverter
    fhir_resource = Patient
    json_repr = 'test/test_patient.json'

    @mock.patch('insuree.models.Gender.objects')
    def test_to_imis_obj(self, mock_gender):
        mock_gender.get.return_value = self._TEST_GENDER
        super(PatientConverterTestCase, self).test_to_imis_obj()

