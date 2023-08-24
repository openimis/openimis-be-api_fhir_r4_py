from api_fhir_r4.converters import CommunicationRequestConverter
from fhir.resources.R4B.communicationrequest import CommunicationRequest
from api_fhir_r4.tests import CommunicationRequestTestMixin
from api_fhir_r4.tests.mixin import ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class CommunicationRequestConverterTestCase(CommunicationRequestTestMixin,
                                            ConvertToFhirTestMixin,
                                            ConvertJsonToFhirTestMixin):
    converter = CommunicationRequestConverter
    fhir_resource = CommunicationRequest
    json_repr = 'test/test_communicationRequest.json'
