from api_fhir_r4.converters import ClaimAdminPractitionerConverter

from fhir.resources.practitioner import Practitioner
from api_fhir_r4.tests import ClaimAdminPractitionerTestMixin
from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class ClaimAdminPractitionerConverterTestCase(ClaimAdminPractitionerTestMixin,
                                              ConvertToImisTestMixin,
                                              ConvertToFhirTestMixin,
                                              ConvertJsonToFhirTestMixin):
    converter = ClaimAdminPractitionerConverter
    fhir_resource = Practitioner
    json_repr = 'test/test_claimAdminPractitioner.json'
