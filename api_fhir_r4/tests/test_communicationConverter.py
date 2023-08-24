from api_fhir_r4.converters import CommunicationConverter
from api_fhir_r4.tests import CommunicationTestMixin
from fhir.resources.R4B.communication import Communication

from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class CommunicationConverterTestCase(CommunicationTestMixin,
                                     ConvertToImisTestMixin,
                                     ConvertToFhirTestMixin,
                                     ConvertJsonToFhirTestMixin):
    converter = CommunicationConverter
    fhir_resource = Communication
    json_repr = 'test/test_communication.json'
