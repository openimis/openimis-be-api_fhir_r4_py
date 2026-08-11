"""
Regression tests for the FHIR access-control fixes in `api_fhir_r4.permissions`
and the viewsets that use them.

Each test class below targets one endpoint whose permission list used to be
empty (`[]`, meaning "no right required") and asserts BOTH directions:

  * a user who does NOT hold the required right gets `403 Forbidden`
  * a user who holds EXACTLY that right (and nothing else - not a superuser,
    not `is_imis_admin`) is let through the permission layer

Restricted users are built with `core.test_helpers.create_test_role` +
`create_test_interactive_user(roles=[role.id])`, which - unlike the
superuser test users used elsewhere in this test suite - does NOT default
to `is_superuser=True`, so the permission checks under test are actually
exercised instead of being bypassed by the admin shortcut.
"""
from dataclasses import dataclass

from graphql_jwt.shortcuts import get_token
from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin
from api_fhir_r4.tests.utils import load_and_replace_json
from core.models import User
from core.test_helpers import (
    create_test_claim_admin,
    create_test_interactive_user,
    create_test_officer,
    create_test_role,
)
from insuree.test_helpers import create_test_insuree
from product.test_helpers import create_test_product


@dataclass
class _DummyContext:
    """Minimal context object required by graphql_jwt's get_token()."""
    user: User


def _restricted_user(perm_names, username):
    """Create a genuinely restricted (non-superuser) test user limited to `perm_names`."""
    role = create_test_role(perm_names=perm_names, name=f"role_{username}")
    return create_test_interactive_user(username=username, roles=[role.id])


def _bearer_headers_for(user):
    token = get_token(user, _DummyContext(user=user))
    return {"Content-Type": "application/json", "HTTP_AUTHORIZATION": f"Bearer {token}"}


class ContractCreatePermissionAPITests(GenericFhirAPITestMixin, APITestCase):
    """
    FHIRApiCoverageRequestPermissions.permissions_post used to be `[]`, so any
    authenticated user could POST /Contract and create a real insurance policy
    regardless of role. It is now PolicyConfig.gql_mutation_create_policies_perms.
    """

    base_url = GeneralConfiguration.get_base_url() + "Contract/"

    # These UUIDs are placeholders hardcoded in test/test_contract.json and are
    # replaced with the real generated UUIDs of the objects created below.
    _TEST_GROUP_UUID = "e8bbb7e4-19ef-4bef-9342-9ab6b9a928d3"
    _TEST_OFFICER_UUID = "ff7db42d-874b-400a-bba7-e59b273ae123"
    _TEST_INSUREE_UUID = "f8c56ada-d76d-4f6c-aad3-cfddc9fb38eb"
    _TEST_PRODUCT_UUID = "8ed8d2d9-2644-4d29-ba37-ab772386cfca"
    _TEST_PRODUCT_CODE = "TE123"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.test_insuree = create_test_insuree(with_family=True)
        cls.test_product = create_test_product(cls._TEST_PRODUCT_CODE, valid=True)
        cls.test_officer = create_test_officer(
            custom_props={"uuid": cls._TEST_OFFICER_UUID}
        )

    def setUp(self):
        super().setUp()
        sub_str = {
            self._TEST_GROUP_UUID: self.test_insuree.family.uuid,
            self._TEST_INSUREE_UUID: self.test_insuree.uuid,
            self._TEST_OFFICER_UUID: self.test_officer.uuid,
            self._TEST_PRODUCT_UUID: self.test_product.uuid,
        }
        self._contract_payload = load_and_replace_json("/test/test_contract.json", sub_str)

    def test_post_forbidden_without_create_policy_right(self):
        user = _restricted_user([], "contract_no_rights")
        headers = _bearer_headers_for(user)

        response = self.client.post(
            self.base_url, data=self._contract_payload, format="json", **headers
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_post_allowed_with_create_policy_right(self):
        user = _restricted_user(
            ["gql_mutation_create_policies_perms"], "contract_with_rights"
        )
        headers = _bearer_headers_for(user)

        response = self.client.post(
            self.base_url, data=self._contract_payload, format="json", **headers
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)


class CoverageEligibilityRequestPermissionAPITests(GenericFhirAPITestMixin, APITestCase):
    """
    FHIRApiCoverageEligibilityRequestPermissions.permissions_post used to be `[]`
    even though POST performs the same real eligibility lookup as GET. It now
    requires the same PolicyConfig.gql_query_eligibilities_perms as GET.
    """

    base_url = GeneralConfiguration.get_base_url() + "CoverageEligibilityRequest/"

    _TEST_CHF_ID = "chfid"  # placeholder hardcoded in test/test_coverageEligibilityRequest.json

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.test_insuree = create_test_insuree(
            with_family=True, custom_props={"chf_id": "CETest1"}
        )

    def setUp(self):
        super().setUp()
        sub_str = {self._TEST_CHF_ID: self.test_insuree.chf_id}
        self._eligibility_payload = load_and_replace_json(
            "/test/test_coverageEligibilityRequest.json", sub_str
        )

    def test_post_forbidden_without_eligibility_right(self):
        user = _restricted_user([], "eligibility_no_rights")
        headers = _bearer_headers_for(user)

        response = self.client.post(
            self.base_url, data=self._eligibility_payload, format="json", **headers
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_post_allowed_with_eligibility_right(self):
        user = _restricted_user(
            ["gql_query_eligibilities_perms"], "eligibility_with_rights"
        )
        headers = _bearer_headers_for(user)

        response = self.client.post(
            self.base_url, data=self._eligibility_payload, format="json", **headers
        )

        # The permission layer is what's under test here, so we only assert the
        # request is not rejected as unauthorized. We deliberately don't assert
        # 200/201: this endpoint currently raises an unrelated pydantic
        # validation error building FHIRCoverageEligibilityRequest from this
        # payload (a pre-existing bug in CoverageEligibilityRequestConverter,
        # not something introduced or fixed by the permission change under
        # test here) and returns 500 - which still proves the permission gate
        # let the request through.
        self.assertNotEqual(
            response.status_code, status.HTTP_403_FORBIDDEN, response.content
        )


class PractitionerClaimAdminPermissionAPITests(GenericFhirAPITestMixin, APITestCase):
    """
    FHIRApiPractitionerClaimAdminPermissions.permissions_get used to be `[]`,
    so any authenticated user could list every claim administrator nationwide.
    It now requires CoreConfig.gql_query_claim_administrator_perms.
    """

    base_url = GeneralConfiguration.get_base_url() + "Practitioner/"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.test_claim_admin = create_test_claim_admin()

    def test_get_ca_forbidden_without_any_practitioner_right(self):
        # Empty role: neither the claim-admin nor the enrolment-officer right is
        # held, so the multiserializer viewset has no eligible serializer at all.
        user = _restricted_user([], "practitioner_no_rights")
        headers = _bearer_headers_for(user)

        response = self.client.get(
            self.base_url, {"resourceType": "ca"}, format="json", **headers
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_ca_allowed_with_claim_administrator_right(self):
        user = _restricted_user(
            ["gql_query_claim_administrator_perms"], "practitioner_ca_rights"
        )
        headers = _bearer_headers_for(user)

        response = self.client.get(
            self.base_url, {"resourceType": "ca"}, format="json", **headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)


class PractitionerEnrolmentOfficerPermissionAPITests(GenericFhirAPITestMixin, APITestCase):
    """
    FHIRApiPractitionerOfficerPermissions.permissions_get used to be `[]`,
    so any authenticated user could list every enrolment officer nationwide.
    It now requires CoreConfig.gql_query_enrolment_officers_perms.
    """

    base_url = GeneralConfiguration.get_base_url() + "Practitioner/"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.test_officer = create_test_officer()

    def test_get_eo_forbidden_without_any_practitioner_right(self):
        user = _restricted_user([], "practitioner_no_rights_eo")
        headers = _bearer_headers_for(user)

        response = self.client.get(
            self.base_url, {"resourceType": "eo"}, format="json", **headers
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_eo_allowed_with_enrolment_officer_right(self):
        user = _restricted_user(
            ["gql_query_enrolment_officers_perms"], "practitioner_eo_rights"
        )
        headers = _bearer_headers_for(user)

        response = self.client.get(
            self.base_url, {"resourceType": "eo"}, format="json", **headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
