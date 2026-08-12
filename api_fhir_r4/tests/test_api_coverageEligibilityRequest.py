import json
import os

from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from insuree.test_helpers import create_test_insuree
from policy.test_helpers import create_test_policy
from product.test_helpers import create_test_product, create_test_product_item, create_test_product_service
from medical.test_helpers import create_test_item, create_test_service


class CoverageEligibilityRequestAPITests(GenericFhirAPITestMixin, APITestCase, LogInMixin):
    base_url = GeneralConfiguration.get_base_url() + "CoverageEligibilityRequest/"
    _test_json_path = "/test/test_coverageEligibilityRequest.json"

    def setUp(self):
        super(CoverageEligibilityRequestAPITests, self).setUp()
        self.get_or_create_user_api()

        dir_path = os.path.dirname(os.path.realpath(__file__))
        json_representation = open(
            dir_path + self._test_json_path
        ).read()
        self._test_request_data = json.loads(json_representation)

        # Setup required data for the eligibility check
        self.insuree = create_test_insuree(with_family=True, custom_props={"chf_id": "chfid"})
        self.product = create_test_product("TESTPROD")
        self.policy = create_test_policy(self.product, self.insuree.family)

        self.item = create_test_item("ITEST")
        self.service = create_test_service("STEST")

        create_test_product_item(self.product, self.item)
        create_test_product_service(self.product, self.service)

    def test_post_should_return_eligibility_response(self):
        response = self.client.post(
            self.base_url, data=self._test_request_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify it returns a CoverageEligibilityResponse
        self.assertEqual(response.data["resourceType"], "CoverageEligibilityResponse")
        self.assertEqual(response.data["outcome"], "complete")
        
        # Verify patient reference matches request
        self.assertEqual(response.data["patient"]["reference"], "Patient/chfid")
        
        # Verify items were resolved
        insurance_items = response.data.get("insurance", [{}])[0].get("item", [])
        self.assertTrue(len(insurance_items) > 0)
