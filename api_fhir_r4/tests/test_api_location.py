from rest_framework.test import APITestCase

from location.models import Location
from fhir.resources.R4B.location import Location as FHIRLocation
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiCreateTestMixin
from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests.utils import load_and_replace_json

class LocationAPITests(GenericFhirAPITestMixin, FhirApiCreateTestMixin,
                       APITestCase):

    base_url = GeneralConfiguration.get_base_url()+'Location/'
    _test_json_path = "/test/test_location.json"
    _TEST_MUNICIPALITY_UUID = 'a82f54bf-d983-4963-a279-490312a96344'
    _TEST_EXPECTED_NAME = "UPDATED_NAME"
    sub_str = {}
    def setUp(self):
        super(LocationAPITests, self).setUp()
        # create level location
        imis_location_region = Location()
        imis_location_region.code = "RT"
        imis_location_region.name = "Test"
        imis_location_region.type = "R"
        imis_location_region.save()

        imis_location_district = Location()
        imis_location_district.code = "RTDT"
        imis_location_district.name = "Test"
        imis_location_district.type = "D"
        imis_location_district.parent = imis_location_region
        imis_location_district.save()

        imis_location_municipality = Location()
        imis_location_municipality.code = "R2D2"
        imis_location_municipality.name = "Test"
        imis_location_municipality.type = "M"
        imis_location_municipality.parent = imis_location_district
        imis_location_municipality.save()
        self.sub_str[self._TEST_MUNICIPALITY_UUID] = imis_location_municipality.uuid
        self._TEST_MUNICIPALITY_UUID =  imis_location_municipality.uuid
        self._test_request_data = load_and_replace_json(self._test_json_path,self.sub_str)

    def verify_updated_obj(self, updated_obj):
        self.assertTrue(isinstance(updated_obj, FHIRLocation))
        self.assertEqual(self._TEST_EXPECTED_NAME, updated_obj.name)

    def update_resource(self, data):
        data['name'] = self._TEST_EXPECTED_NAME
