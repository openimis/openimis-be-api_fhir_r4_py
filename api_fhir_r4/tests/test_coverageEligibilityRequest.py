import json
import os

from api_fhir_r4.converters import CoverageEligibilityRequestConverter
from api_fhir_r4.tests import CoverageEligibilityRequestTestMixin
from fhir.resources.R4B.coverageeligibilityresponse import CoverageEligibilityResponse


class CoverageEligibilityRequestConverterTestCase(CoverageEligibilityRequestTestMixin):

    __TEST_COVERAGE_ELIGIBILITY_RESPONSE_JSON_PATH = "/test/test_coverageEligibilityResponse.json"
    __TEST_COVERAGE_ELIGIBILITY_REQUEST_JSON_PATH = "/test/test_coverageEligibilityRequest.json"

    def setUp(self):
        super(CoverageEligibilityRequestConverterTestCase, self).setUp()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self._test_coverage_eligibility_response_json_representation = open(dir_path
                                                                   + self.__TEST_COVERAGE_ELIGIBILITY_RESPONSE_JSON_PATH) \
            .read()
        self._test_coverage_eligibility_request_json_representation = open(dir_path
                                                                  + self.__TEST_COVERAGE_ELIGIBILITY_REQUEST_JSON_PATH) \
            .read()

    #def test_to_fhir_obj(self):
        #imis_coverage_eligibility_response = self.create_test_imis_instance()
        #fhir_coverage_eligibility_response = CoverageEligibilityRequestConverter.to_fhir_obj(imis_coverage_eligibility_response)
        #self.verify_fhir_instance(fhir_coverage_eligibility_response)

    def test_to_imis_obj(self):
        fhir_coverage_eligibility_request = self.create_test_fhir_instance()
        imis_coverage_eligibility_request = CoverageEligibilityRequestConverter.to_imis_obj(fhir_coverage_eligibility_request.dict(), None)
        self.verify_imis_instance(imis_coverage_eligibility_request)

    def test_create_object_from_json(self):
        dict_coverage_eligibility_response = json.loads(self._test_coverage_eligibility_response_json_representation)
        fhir_coverage_eligibility_response = CoverageEligibilityResponse(**dict_coverage_eligibility_response)
        self.verify_fhir_instance(fhir_coverage_eligibility_response)
