from api_fhir_r4.converters import ClaimResponseConverter
from api_fhir_r4.models import ClaimResponseV2 as ClaimResponse
from api_fhir_r4.tests import ClaimResponseTestMixin
from api_fhir_r4.tests.mixin import ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class ClaimResponseConverterTestCase(ClaimResponseTestMixin,
                                     ConvertToFhirTestMixin,
                                     ConvertJsonToFhirTestMixin):
    converter = ClaimResponseConverter
    fhir_resource = ClaimResponse
    json_repr = 'test/test_claimResponse.json'
