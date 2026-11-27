"""
OP-3351 / CVE-2026-82494: who may see a FHIR subscription, subscribe to a resource,
and receive a notification for a given instance.

* Listing: 158001 (`query`) shows the caller's own subscriptions only; 158005
  (`query_all`) shows every subscription; neither is refused.
* Subscribing: the caller must hold the read right of the model behind the
  `criteria` resource, as the model declares it (`Model.get_rights`), so a right
  overridden in ModuleConfiguration is honoured.
* Notifying: each subscription is authorized for its owner and for the instance
  that changed - owner still active, still holding the read right, instance inside
  the owner's row scope - and the resource is converted as that owner.
"""
import datetime
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.converters import ClaimResponseConverter
from api_fhir_r4.models import Subscription, SubscriptionNotificationResult
from api_fhir_r4.signals import notify_subscribers
from api_fhir_r4.subscriptions.notificationClient import SubscriberNotificationOutput
from api_fhir_r4.tests import CommunicationTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from claim.apps import ClaimConfig
from claim.models import Claim
from core.models import InteractiveUser
from core.utils import get_current_user
from core.test_helpers import create_test_interactive_user, create_test_role
from location.models import HealthFacility, Location
from location.test_helpers import assign_user_districts, create_test_location

SUB_QUERY = "fhir_sub_search_perms"
SUB_QUERY_ALL = "fhir_sub_search_all_perms"
SUB_CREATE = "fhir_sub_create_perms"
CLAIM_QUERY = "gql_query_claims_perms"


def _user_with(username, perm_names):
    role = create_test_role(perm_names, name=f"OP3351 {username}")
    return create_test_interactive_user(username=username, roles=[role.id])


def _subscription(owner, criteria):
    sub = Subscription(
        status=Subscription.SubscriptionStatus.ACTIVE,
        channel=Subscription.SubscriptionChannel.REST_HOOK,
        endpoint="https://subscriber.example.org/hook",
        headers="Key=Value",
        criteria=criteria,
        expiring=datetime.datetime.now() + datetime.timedelta(days=10),
    )
    sub.save(username=owner.username)
    return sub


class SubscriptionListingRightsTest(APITestCase):
    base_url = GeneralConfiguration.get_base_url() + "Subscription/"

    def setUp(self):
        self.own_user = _user_with("op3351_own", [SUB_QUERY])
        self.other_user = _user_with("op3351_other", [SUB_QUERY])
        self.no_right_user = _user_with("op3351_none", [SUB_CREATE])
        self.own_sub = _subscription(self.own_user, {"resource": "Patient"})
        self.other_sub = _subscription(self.other_user, {"resource": "Patient"})

    def _listed_ids(self, user):
        self.client.force_authenticate(user=user)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        return {entry["resource"]["id"] for entry in response.json().get("entry", [])}

    def test_query_right_lists_only_own_subscriptions(self):
        listed = self._listed_ids(self.own_user)
        self.assertIn(str(self.own_sub.id), listed)
        self.assertNotIn(str(self.other_sub.id), listed)

    def test_query_right_cannot_read_another_users_subscription(self):
        self.client.force_authenticate(user=self.own_user)
        response = self.client.get(f"{self.base_url}{self.other_sub.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_query_all_right_lists_every_subscription(self):
        all_user = _user_with("op3351_all", [SUB_QUERY_ALL])
        listed = self._listed_ids(all_user)
        self.assertIn(str(self.own_sub.id), listed)
        self.assertIn(str(self.other_sub.id), listed)

    def test_no_query_right_is_refused(self):
        self.client.force_authenticate(user=self.no_right_user)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubscriptionCreateResourceRightsTest(APITestCase):
    base_url = GeneralConfiguration.get_base_url() + "Subscription/"

    def _payload(self, criteria):
        return {
            "resourceType": "Subscription",
            "status": "active",
            "end": (datetime.datetime.now() + datetime.timedelta(days=10)).strftime(
                "%Y-%m-%dT%H:%M:%S+00:00"
            ),
            "reason": criteria.split("?")[0],
            "criteria": criteria,
            "channel": {
                "type": "rest-hook",
                "endpoint": "https://subscriber.example.org/hook",
                "header": ["Key=Value"],
            },
        }

    def _post(self, user, criteria):
        self.client.force_authenticate(user=user)
        return self.client.post(self.base_url, data=self._payload(criteria), format="json")

    def test_claim_subscription_without_claim_right_is_refused(self):
        user = _user_with("op3351_creator", [SUB_CREATE])
        response = self._post(user, "Claim?code=OP3351")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
        self.assertFalse(Subscription.objects.filter(user_created=user).exists())

    def test_claim_subscription_with_claim_right_is_accepted(self):
        user = _user_with("op3351_claim_creator", [SUB_CREATE, CLAIM_QUERY])
        response = self._post(user, "Claim?code=OP3351")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

    def test_claim_right_overridden_in_configuration_is_honoured(self):
        """The model's configured right decides, not a list fixed at import time."""
        user = _user_with("op3351_claim_override", [SUB_CREATE, CLAIM_QUERY])
        with patch.object(ClaimConfig, "gql_query_claims_perms", ["999999"]):
            response = self._post(user, "Claim?code=OP3351")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)


class _FakeFhirResource:
    def __init__(self, username):
        self.username = username

    def dict(self):
        return {"converted_as": self.username}


class SubscriptionNotificationAuthorizationTest(CommunicationTestMixin, LogInMixin, TestCase):
    """A change to a claim, notified to four subscribers of which only one may read it."""

    def setUp(self):
        super().setUp()
        self.claim = self._TEST_CLAIM
        district = self._district_of(self.claim.health_facility.location)
        # A health facility belongs to a district; the test context puts it on the
        # insuree's village, which the claim's district scope never matches.
        HealthFacility.objects.filter(pk=self.claim.health_facility_id).update(
            location=district
        )
        self.claim = Claim.objects.get(pk=self.claim.pk)
        other_district = create_test_location(
            "D", custom_props={"code": "OP3351D", "parent": district.parent}
        )

        self.allowed = _user_with("op3351_sub_ok", [CLAIM_QUERY])
        assign_user_districts(self.allowed, [district.code])
        self.no_right = _user_with("op3351_sub_noright", [])
        assign_user_districts(self.no_right, [district.code])
        self.out_of_scope = _user_with("op3351_sub_scope", [CLAIM_QUERY])
        assign_user_districts(self.out_of_scope, [other_district.code])
        self.deleted = _user_with("op3351_sub_deleted", [CLAIM_QUERY])
        assign_user_districts(self.deleted, [district.code])

        # The scenario only proves something if row scope really separates them.
        in_claim = Claim.objects.filter(pk=self.claim.pk)
        self.assertTrue(Claim.get_queryset(in_claim, self.allowed).exists())
        self.assertFalse(Claim.get_queryset(in_claim, self.out_of_scope).exists())

        criteria = {"resource": "Claim"}
        self.sub_allowed = _subscription(self.allowed, criteria)
        self.sub_no_right = _subscription(self.no_right, criteria)
        self.sub_out_of_scope = _subscription(self.out_of_scope, criteria)
        self.sub_deleted = _subscription(self.deleted, criteria)
        InteractiveUser.objects.filter(pk=self.deleted.i_user.pk).update(
            active=False, validity_to=datetime.datetime.now()
        )

        # The change is made by an administrator, who could read anything.
        self.actor = self.get_or_create_user_api()

    @staticmethod
    def _district_of(location):
        while location is not None and location.type != "D":
            location = location.parent
        if location is None:
            raise AssertionError("the test claim's health facility has no district")
        return Location.objects.get(pk=location.pk)

    def _notify(self):
        sent = []

        def propagate(content, subscribers):
            sent.append((content, list(subscribers)))
            return [SubscriberNotificationOutput(s, True) for s in subscribers]

        def to_fhir_obj(obj, reference_type):
            # Converters are classmethods: "as a user" means the current user while
            # the conversion runs.
            return _FakeFhirResource(get_current_user().username)

        with patch(
            "api_fhir_r4.subscriptions.notificationManager.RestSubscriptionNotificationClient"
        ) as client_cls, patch.object(
            ClaimResponseConverter, "to_fhir_obj", side_effect=to_fhir_obj
        ):
            client_cls.return_value.propagate_notifications.side_effect = propagate
            notify_subscribers(
                self.claim, ClaimResponseConverter(user=self.actor), "Claim", None
            )
        return sent

    def _recipients(self, sent):
        return {sub.id for _, subscribers in sent for sub in subscribers}

    def _rejection(self, subscription):
        results = SubscriptionNotificationResult.objects.subscriber_notifications(subscription)
        self.assertEqual(results.count(), 1, f"expected one recorded result for {subscription.id}")
        result = results.first()
        self.assertFalse(result.notified_successfully)
        self.assertTrue(result.error)
        return result.error

    def test_subscriber_with_right_and_scope_is_notified_as_themselves(self):
        sent = self._notify()
        self.assertIn(self.sub_allowed.id, self._recipients(sent))
        payloads = [
            content for content, subscribers in sent
            if self.sub_allowed.id in {s.id for s in subscribers}
        ]
        self.assertEqual(payloads, [{"converted_as": self.allowed.username}])
        # The request carries on as the user who made the change.
        self.assertEqual(get_current_user(), self.actor)
        result = SubscriptionNotificationResult.objects.subscriber_notifications(
            self.sub_allowed
        ).get()
        self.assertTrue(result.notified_successfully)

    def test_subscriber_without_the_claim_right_is_not_notified(self):
        sent = self._notify()
        self.assertNotIn(self.sub_no_right.id, self._recipients(sent))
        self.assertIn("right", self._rejection(self.sub_no_right))

    def test_subscriber_scoped_to_another_district_is_not_notified(self):
        sent = self._notify()
        self.assertNotIn(self.sub_out_of_scope.id, self._recipients(sent))
        self.assertIn("scope", self._rejection(self.sub_out_of_scope))

    def test_subscriber_whose_user_is_deleted_is_not_notified(self):
        sent = self._notify()
        self.assertNotIn(self.sub_deleted.id, self._recipients(sent))
        self.assertIn("inactive", self._rejection(self.sub_deleted))
