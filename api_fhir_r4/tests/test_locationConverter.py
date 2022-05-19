from api_fhir_r4.converters.locationConverter import LocationConverter
from fhir.resources.location import Location
from api_fhir_r4.tests import LocationTestMixin
from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class LocationConverterTestCase(LocationTestMixin,
                                ConvertToImisTestMixin,
                                ConvertToFhirTestMixin,
                                ConvertJsonToFhirTestMixin):
    converter = LocationConverter
    fhir_resource = Location
    json_repr = 'test/test_location.json'
