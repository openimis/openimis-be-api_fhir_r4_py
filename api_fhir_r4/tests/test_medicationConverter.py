from api_fhir_r4.converters import MedicationConverter

from fhir.resources.R4B.medication import Medication
from api_fhir_r4.tests import MedicationTestMixin
from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class MedicationConverterTestCase(MedicationTestMixin,
                                  ConvertToImisTestMixin,
                                  ConvertToFhirTestMixin,
                                  ConvertJsonToFhirTestMixin):
    converter = MedicationConverter
    fhir_resource = Medication
    json_repr = 'test/test_medication.json'
