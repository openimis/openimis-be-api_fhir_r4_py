from location.models import Location

from api_fhir_r4.configurations import R4IdentifierConfig, R4LocationConfig
from api_fhir_r4.converters import LocationConverter
from fhir.resources.R4B.location import Location as FHIRLocation
from api_fhir_r4.tests import GenericTestMixin
from location.test_helpers import create_test_location, create_test_health_facility, create_test_village


class LocationTestMixin(GenericTestMixin):

    _TEST_VILLAGE_CODE = "RTDTMTVT"
    _TEST_VILLAGE_NAME = "TEST_NAME"
    _TEST_LOCATION_TYPE = "V"
    test_region = None
    test_district = None
    test_village = None
    test_ward = None
    
    def setUp(self):
        super().setUp()
        if self.test_region is None:
            self.test_village  =create_test_village( custom_props={"code":self._TEST_VILLAGE_CODE,"name":self._TEST_VILLAGE_NAME})
            self.test_ward =self.test_village.parent
            self.test_region =self.test_village.parent.parent.parent
            self.test_district = self.test_village.parent.parent
    
    def create_test_imis_instance(self):
        return self.test_village

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_VILLAGE_CODE, imis_obj.code)
        self.assertEqual(self._TEST_VILLAGE_NAME, imis_obj.name)
        self.assertEqual(self._TEST_LOCATION_TYPE, imis_obj.type)

    def create_test_fhir_instance(self):
        fhir_location = FHIRLocation.construct()
        identifier = LocationConverter.build_fhir_identifier(self._TEST_VILLAGE_CODE,
                                                             R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                             R4IdentifierConfig.get_fhir_location_code_type())
        fhir_location.identifier = [identifier]

        fhir_location.name = self._TEST_VILLAGE_NAME

        system_definition = LocationConverter.PHYSICAL_TYPES.get(self._TEST_LOCATION_TYPE)
        fhir_location.physicalType = LocationConverter.build_codeable_concept(**system_definition)

        fhir_location.mode = 'instance'
        fhir_location.status = R4LocationConfig.get_fhir_code_for_active()

        return fhir_location

    def verify_fhir_instance(self, fhir_obj):
        for identifier in fhir_obj.identifier:
            code = LocationConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_uuid_type_code():
                self.assertEqual(fhir_obj.id, identifier.value)
            elif code == R4IdentifierConfig.get_fhir_facility_id_type():
                self.assertEqual(self._TEST_VILLAGE_CODE, identifier.value)
        self.assertEqual(self._TEST_VILLAGE_NAME, fhir_obj.name)
        physical_type_code = LocationConverter.get_first_coding_from_codeable_concept(fhir_obj.physicalType).code
        self.assertEqual(self._TEST_LOCATION_TYPE, physical_type_code)
        self.assertEqual(R4LocationConfig.get_fhir_code_for_active(), fhir_obj.status)
        self.assertEqual('instance', fhir_obj.mode)
