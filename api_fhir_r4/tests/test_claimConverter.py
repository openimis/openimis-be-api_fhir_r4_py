from api_fhir_r4.converters.claimConverter import ClaimConverter
from api_fhir_r4.models import ClaimV2 as Claim
from api_fhir_r4.tests import ClaimTestMixin
from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class ClaimConverterTestCase(ClaimTestMixin,
                             ConvertToImisTestMixin,
                             ConvertToFhirTestMixin,
                             ConvertJsonToFhirTestMixin):
    converter = ClaimConverter
    fhir_resource = Claim
    json_repr = 'test/test_claim.json'
