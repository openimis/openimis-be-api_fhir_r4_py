from api_fhir_r4.converters import OperationOutcomeConverter
from api_fhir_r4.models import OperationOutcomeV2
from api_fhir_r4.tests import OperationOutcomeTestMixin
from api_fhir_r4.tests.mixin import ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class OperationOutcomeConverterTestCase(OperationOutcomeTestMixin,
                                        ConvertToFhirTestMixin,
                                        ConvertJsonToFhirTestMixin):
    converter = OperationOutcomeConverter
    fhir_resource = OperationOutcomeV2
    json_repr = 'test/test_outcome.json'
