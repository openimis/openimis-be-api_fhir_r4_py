from api_fhir_r4.converters import EnrolmentOfficerPractitionerConverter

from fhir.resources.R4B.practitioner import Practitioner
from api_fhir_r4.tests import EnrolmentOfficerPractitionerTestMixin
from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class EnrolmentOfficerPractitionerConverterTestCase(EnrolmentOfficerPractitionerTestMixin,
                                                    ConvertToImisTestMixin,
                                                    ConvertToFhirTestMixin,
                                                    ConvertJsonToFhirTestMixin):
    converter = EnrolmentOfficerPractitionerConverter
    fhir_resource = Practitioner
    json_repr = 'test/test_enrolmentOfficerPractitioner.json'
