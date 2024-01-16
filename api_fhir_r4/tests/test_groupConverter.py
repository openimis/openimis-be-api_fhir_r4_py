from api_fhir_r4.converters import GroupConverter

from fhir.resources.R4B.group import Group
from api_fhir_r4.tests import GroupTestMixin
from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class GroupConverterTestCase(GroupTestMixin,
                             ConvertToImisTestMixin,
                             ConvertToFhirTestMixin,
                             ConvertJsonToFhirTestMixin):
    converter = GroupConverter
    fhir_resource = Group
    json_repr = 'test/test_group.json'
