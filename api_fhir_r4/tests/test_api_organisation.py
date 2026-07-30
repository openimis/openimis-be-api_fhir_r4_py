
from fhir.resources.R4B.organization import Organization
from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import (
    GenericFhirAPITestMixin,
    FhirApiReadTestMixin,
    LocationTestMixin,
)
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from policyholder.models import PolicyHolder
from location.test_helpers import create_test_health_facility
from api_fhir_r4.tests.utils import load_and_replace_json


class OrganisationAPITests(
    GenericFhirAPITestMixin,
    FhirApiReadTestMixin,
    LocationTestMixin,
    APITestCase,
    LogInMixin,
):
    base_url = GeneralConfiguration.get_base_url() + "Organization/"
    _test_json_path = "/test/test_organisation.json"
    _TEST_PH_CODE = "TestPHCode"
    _TEST_PH_NAME = "Test PolicyHolder"

    _test_json_path_credentials = "/test/test_login.json"

    _test_request_data_credentials = None
    _test_request_data = None
    sub_str = {}

    def get_all_bundle_entries(self, url):
        all_entries = []
        current_url = url
        while current_url:
            response = self.client.get(current_url, format="json")
            self.assertEqual(
                response.status_code, status.HTTP_200_OK, str(response.content)
            )
            bundle = self.get_bundle_from_json_response(response)
            if bundle.entry:
                all_entries.extend(bundle.entry)
            next_url = None
            if bundle.link:
                for link in bundle.link:
                    if link.relation == "next":
                        next_url = self._sanitize_next_url(link.url)
                        break
            current_url = next_url
        return all_entries

    def _sanitize_next_url(self, next_url):
        """Sanitize the next URL by replacing only the query parameters, keeping the base URL from prev_url."""
        try:
            from urllib.parse import urlparse, urlunparse, parse_qs
        except ImportError:
            from urlparse import urlparse, urlunparse, parse_qs

        # Parse the next URL to get the query parameters
        next_parsed = urlparse(next_url)
        parse_qs(next_parsed.query)

        # Combine base URL with sanitized query parameters
        sanitized_url = urlunparse(
            ("", "", next_parsed.path, "", next_parsed.query, "")
        )

        return sanitized_url

    def setUp(self):
        super(OrganisationAPITests, self).setUp()
        LocationTestMixin.setUp(self)

        self.get_or_create_user_api()
        self.create_dependencies()

        self.sub_str[self._TEST_PH_CODE] = self._TEST_PH_CODE
        self.sub_str[self._TEST_PH_NAME] = self._TEST_PH_NAME

        self._test_request_data = load_and_replace_json(
            self._test_json_path, self.sub_str
        )

    def verify_updated_obj(self, updated_obj):
        self.assertTrue(isinstance(updated_obj, Organization))
        self.assertEqual(updated_obj.name, self._TEST_PH_NAME)

    def update_resource(self, data):
        data["name"] = self._TEST_PH_NAME

    def create_dependencies(self):
        pass

    def test_post_should_create_correctly(self):
        self.login()
        response = self.client.post(
            self.base_url, data=self._test_request_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify that a PolicyHolder was created
        ph = PolicyHolder.objects.filter(code=self._TEST_PH_CODE).first()
        self.assertIsNotNone(ph)
        self.assertEqual(ph.trade_name, self._TEST_PH_NAME)

    def test_get_list_should_return_policyholders(self):
        # Create multiple policyholders
        self.login()
        # Create first policyholder
        response1 = self.client.post(
            self.base_url, data=self._test_request_data, format="json"
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Create second policyholder with different data
        sub_str_2 = {
            "TestPHCode": "TestPHCode2",
            "Test PolicyHolder": "Test PolicyHolder 2",
        }
        test_data_2 = load_and_replace_json(self._test_json_path, sub_str_2)
        response2 = self.client.post(self.base_url, data=test_data_2, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Get list of policyholders with type=bus
        bus_entries = self.get_all_bundle_entries(self.base_url + "?type=bus")
        self.assertGreaterEqual(len(bus_entries), 2)

        # Verify the policyholders are in the bundle
        found_ph1 = False
        found_ph2 = False
        for entry in bus_entries:
            if hasattr(entry.resource, "name"):
                if entry.resource.name == self._TEST_PH_NAME:
                    found_ph1 = True
                elif entry.resource.name == "Test PolicyHolder 2":
                    found_ph2 = True

        self.assertTrue(found_ph1, "First policyholder not found in list")
        self.assertTrue(found_ph2, "Second policyholder not found in list")

    def test_get_list_should_return_health_facilities(self):
        # Create multiple health facilities
        self.login()

        # Create first health facility
        create_test_health_facility(
            "HF001",
            self.test_village.parent.parent_id,
            custom_props={"name": "Test Health Facility 1"},
        )
        # Create second health facility
        create_test_health_facility(
            "HF002",
            self.test_village.parent.parent_id,
            custom_props={"name": "Test Health Facility 2"},
        )

        # Get list of health facilities with type=prov
        prov_entries = self.get_all_bundle_entries(self.base_url + "?type=prov")
        self.assertGreaterEqual(len(prov_entries), 2)

        # Verify the health facilities are in the bundle
        found_hf1 = False
        found_hf2 = False
        for entry in prov_entries:
            if hasattr(entry.resource, "name"):
                if entry.resource.name == "Test Health Facility 1":
                    found_hf1 = True
                elif entry.resource.name == "Test Health Facility 2":
                    found_hf2 = True

        self.assertTrue(found_hf1, "First health facility not found in list")
        self.assertTrue(found_hf2, "Second health facility not found in list")

    def test_get_list_should_return_insurance_organizations(self):
        # Test insurance organizations list with type=ins
        self.login()

        # Get list of insurance organizations with type=ins
        ins_entries = self.get_all_bundle_entries(self.base_url + "?type=ins")
        self.assertGreaterEqual(len(ins_entries), 1)

        # Verify the insurance organization is in the bundle
        found_ins = False
        for entry in ins_entries:
            if hasattr(entry.resource, "name"):
                # Insurance organizations should have a name
                found_ins = True
                break

        self.assertTrue(found_ins, "Insurance organization not found in list")

    def test_type_filter_should_work_correctly(self):
        # Create organizations of different types and verify type filtering
        self.login()

        # Create a policyholder
        response_ph = self.client.post(
            self.base_url, data=self._test_request_data, format="json"
        )
        self.assertEqual(response_ph.status_code, status.HTTP_201_CREATED)

        # Create health facilities
        create_test_health_facility(
            "HF001",
            self.test_village.parent.parent_id,
            custom_props={"name": "Test Health Facility 1"},
        )

        # Get all organizations without type filter
        all_entries = self.get_all_bundle_entries(self.base_url)

        # Get policyholders only (type=bus)
        bus_entries = self.get_all_bundle_entries(self.base_url + "?type=bus")

        # Get health facilities only (type=prov)
        prov_entries = self.get_all_bundle_entries(self.base_url + "?type=prov")

        # Get insurance organizations only (type=ins)
        ins_entries = self.get_all_bundle_entries(self.base_url + "?type=ins")

        # Verify that different type filters return different results
        # All should have entries
        self.assertGreater(len(all_entries), 0)
        self.assertGreater(len(bus_entries), 0)
        self.assertGreater(len(prov_entries), 0)
        self.assertGreater(len(ins_entries), 0)

        # Policyholders should be in bus but not in prov or ins
        bus_names = [
            entry.resource.name
            for entry in bus_entries
            if hasattr(entry.resource, "name")
        ]
        prov_names = [
            entry.resource.name
            for entry in prov_entries
            if hasattr(entry.resource, "name")
        ]
        ins_names = [
            entry.resource.name
            for entry in ins_entries
            if hasattr(entry.resource, "name")
        ]

        # Policyholder should be in bus results
        self.assertIn(self._TEST_PH_NAME, bus_names)

        # Policyholder should NOT be in prov or ins results
        self.assertNotIn(self._TEST_PH_NAME, prov_names)
        self.assertNotIn(self._TEST_PH_NAME, ins_names)

        # Health facility should be in prov results
        self.assertIn("Test Health Facility 1", prov_names)

        # Health facility should NOT be in bus or ins results
        self.assertNotIn("Test Health Facility 1", bus_names)
        self.assertNotIn("Test Health Facility 1", ins_names)

    def test_get_list_without_filter_should_return_all_organizations(self):
        # Test that without type filter, all organization types are returned
        self.login()

        # Create a policyholder
        response_ph = self.client.post(
            self.base_url, data=self._test_request_data, format="json"
        )
        self.assertEqual(response_ph.status_code, status.HTTP_201_CREATED)

        # Create a health facility
        create_test_health_facility(
            "HF001",
            self.test_village.parent.parent_id,
            custom_props={"name": "Test Health Facility"},
        )

        # Get all organizations without type filter
        all_entries = self.get_all_bundle_entries(self.base_url)
        self.assertGreaterEqual(
            len(all_entries), 3
        )  # At least policyholder, health facility, and insurance organization

        # Collect all organization names
        all_names = [
            entry.resource.name
            for entry in all_entries
            if hasattr(entry.resource, "name")
        ]

        # Verify that organizations from all types are present
        self.assertIn(
            self._TEST_PH_NAME,
            all_names,
            "Policyholder not found in unfiltered results",
        )
        self.assertIn(
            "Test Health Facility",
            all_names,
            "Health facility not found in unfiltered results",
        )

        # Insurance organization should also be present (from default config)
        # We can't check the exact name since it comes from config, but we know there should be at least one
        insurance_orgs = [
            name
            for name in all_names
            if name not in [self._TEST_PH_NAME, "Test Health Facility"]
        ]
        self.assertGreaterEqual(
            len(insurance_orgs),
            1,
            "Insurance organization not found in unfiltered results",
        )
