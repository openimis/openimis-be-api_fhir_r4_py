from location.models import Location

from api_fhir_r4.configurations import R4IdentifierConfig, R4LocationConfig
from api_fhir_r4.converters import LocationConverter
from fhir.resources.location import Location as FHIRLocation
from api_fhir_r4.tests import GenericTestMixin


class LocationTestMixin(GenericTestMixin):

    _TEST_CODE = "RTDTMTVT"
    _TEST_NAME = "TEST_NAME"
    _TEST_LOCATION_TYPE = "V"
    _TEST_MUNICIPALITY_UUID = "a82f54bf-d983-4963-a279-490312a96344"

    def create_test_imis_instance(self):
        # create level location
        imis_location_region = Location()
        imis_location_region.code = "RT"
        imis_location_region.name = self._TEST_NAME
        imis_location_region.type = "R"
        imis_location_region.save()

        imis_location_district = Location()
        imis_location_district.code = "RTDT"
        imis_location_district.name = self._TEST_NAME
        imis_location_district.type = "D"
        imis_location_district.parent = imis_location_region
        imis_location_district.save()

        imis_location_municipality = Location()
        imis_location_municipality.code = "RTDTMT"
        imis_location_municipality.name = self._TEST_NAME
        imis_location_municipality.type = "M"
        imis_location_municipality.parent = imis_location_district
        imis_location_municipality.uuid = self._TEST_MUNICIPALITY_UUID
        imis_location_municipality.save()

        imis_location = Location()
        imis_location.code = self._TEST_CODE
        imis_location.name = self._TEST_NAME
        imis_location.type = self._TEST_LOCATION_TYPE
        imis_location.parent = imis_location_municipality
        return imis_location

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_CODE, imis_obj.code)
        self.assertEqual(self._TEST_NAME, imis_obj.name)
        self.assertEqual(self._TEST_LOCATION_TYPE, imis_obj.type)

    def create_test_fhir_instance(self):
        fhir_location = FHIRLocation.construct()
        identifier = LocationConverter.build_fhir_identifier(self._TEST_CODE,
                                                             R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                             R4IdentifierConfig.get_fhir_location_code_type())
        fhir_location.identifier = [identifier]

        fhir_location.name = self._TEST_NAME

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
                self.assertEqual(self._TEST_CODE, identifier.value)
        self.assertEqual(self._TEST_NAME, fhir_obj.name)
        physical_type_code = LocationConverter.get_first_coding_from_codeable_concept(fhir_obj.physicalType).code
        self.assertEqual(self._TEST_LOCATION_TYPE, physical_type_code)
        self.assertEqual(R4LocationConfig.get_fhir_code_for_active(), fhir_obj.status)
        self.assertEqual('instance', fhir_obj.mode)
