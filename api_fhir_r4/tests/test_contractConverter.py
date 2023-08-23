from api_fhir_r4.converters import ContractConverter
from api_fhir_r4.tests import ContractTestMixin
from fhir.resources.R4B.contract import Contract

from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class ContractConverterTestCase(ContractTestMixin,
                                ConvertToImisTestMixin,
                                ConvertToFhirTestMixin,
                                ConvertJsonToFhirTestMixin):
    converter = ContractConverter
    fhir_resource = Contract
    json_repr = 'test/test_contract.json'
