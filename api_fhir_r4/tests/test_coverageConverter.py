from api_fhir_r4.converters.coverageConverter import CoverageConverter
from api_fhir_r4.tests import CoverageTestMixin
from api_fhir_r4.models import CoverageV2 as Coverage
from api_fhir_r4.tests.mixin import ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class CoverageConverterTestCase(CoverageTestMixin,
                                ConvertToFhirTestMixin,
                                ConvertJsonToFhirTestMixin):
    converter = CoverageConverter
    fhir_resource = Coverage
    json_repr = 'test/test_coverage.json'
