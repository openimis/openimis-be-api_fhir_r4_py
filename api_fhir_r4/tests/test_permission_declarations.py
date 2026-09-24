"""
Guard rails on api_fhir_r4's rights declaration.

Same structure as `claim`, `core` or `api_etl`: `DJANGO_PERMS` by entity then by
action, `_PERM_CFG` deriving the config keys from it, and `Subscription.get_rights` as
the access point. What is particular to this module is that it has almost no rights of
its own: its REST/FHIR layer *borrows* those of the business modules
(`api_fhir_r4/rights.py`). Only the FHIR subscription belongs to it - a concept with no
GraphQL equivalent, whose model lives here - and that is the only thing `DJANGO_PERMS`
has to declare.

What is locked down here:
  * the identifiers 158001-158004, as deployed and as `permissions_map.json` carries
    them - changing one withdraws access from the roles that hold it;
  * the fact that `DJANGO_PERMS` **redeclares no borrowed right**: another module's
    identifier copied here would be a second definition, free to diverge;
  * a config key with no class attribute is never loaded and reading it raises
    AttributeError - the right becomes unenforceable;
  * `has_perms([])` returns True, so an empty list grants to everybody.
"""

import json
import os

from django.test import TestCase

from api_fhir_r4.apps import (
    DJANGO_PERMS,
    ApiFhirConfig,
    _PERM_CFG,
    configured_perms,
    django_perms,
    perms,
)
from api_fhir_r4.models import Subscription
from api_fhir_r4.models.subscription import SubscriptionNotificationResult

# The identifiers as deployed. Changing one is incompatible with the existing roles:
# this test has to be updated *and* the new right granted.
EXPECTED_RIGHTS = {
    "fhir_sub_search_perms": ["158001"],
    "fhir_sub_create_perms": ["158002"],
    "fhir_sub_update_perms": ["158003"],
    "fhir_sub_delete_perms": ["158004"],
}

# The `permissions_map.json` keys that carry these same identifiers.
EXPECTED_MAP_ENTRIES = {
    "api_fhir_r4.fhir_sub_search": "158001",
    "api_fhir_r4.fhir_sub_create": "158002",
    "api_fhir_r4.fhir_sub_update": "158003",
    "api_fhir_r4.fhir_sub_delete": "158004",
}


def _load_permissions_map():
    """`permissions_map.json` lives in the assembly, not in the package."""
    from django.conf import settings

    candidates = [
        os.path.join(str(settings.BASE_DIR), "permissions_map.json"),
        os.path.join(os.path.dirname(str(settings.BASE_DIR)), "permissions_map.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path) as handle:
                return json.load(handle)
    return None


class ApiFhirR4PermissionDeclarationTestCase(TestCase):
    def test_right_ids_unchanged(self):
        self.assertEqual(
            {key: getattr(ApiFhirConfig, key) for key in EXPECTED_RIGHTS},
            EXPECTED_RIGHTS,
        )

    def test_perm_cfg_covers_every_declared_action(self):
        declared = {
            (entity, action)
            for entity, actions in DJANGO_PERMS.items()
            for action in actions
        }
        self.assertEqual(set(_PERM_CFG.values()), declared)

    def test_perm_cfg_matches_config_attributes(self):
        missing = [key for key in _PERM_CFG if not hasattr(ApiFhirConfig, key)]
        self.assertEqual(missing, [])

    def test_no_right_list_is_empty(self):
        empty = [key for key in _PERM_CFG if not getattr(ApiFhirConfig, key)]
        self.assertEqual(empty, [])

    def test_attributes_carry_the_declared_right(self):
        """
        The rights are constants set from DJANGO_PERMS: the attribute must equal the
        declaration, without going through the config.
        """
        for key, (entity, action) in _PERM_CFG.items():
            with self.subTest(key=key):
                self.assertEqual(getattr(ApiFhirConfig, key), perms(entity, action))

    # --- the module declares only what belongs to it ----------------------
    def test_only_the_subscription_entity_is_declared(self):
        """
        The rights the FHIR layer borrows from the business modules are not redeclared
        here: their source of truth is the owner's `DJANGO_PERMS`, reachable through
        `Model.get_rights(action)`.
        """
        self.assertEqual(set(DJANGO_PERMS), {"subscription"})

    def test_every_declared_id_is_in_this_module_block(self):
        """158xxx is this module's block in the openIMIS catalogue."""
        for entity, actions in DJANGO_PERMS.items():
            for action, (_, right_id) in actions.items():
                with self.subTest(entity=entity, action=action):
                    self.assertTrue(158000 <= right_id < 159000, right_id)

    def test_no_shared_right_ids(self):
        """No identifier sharing is intended in this module."""
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (_, right_id) in actions.items():
                seen.setdefault(right_id, []).append((entity, action))
        shared = {rid: who for rid, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_are_unique(self):
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                seen.setdefault(name, []).append(f"{entity}.{action}")
        shared = {name: who for name, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_use_the_app_label(self):
        """The Subscription model's app_label in this assembly is `api_fhir_r4`."""
        self.assertEqual(Subscription._meta.app_label, "api_fhir_r4")
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                with self.subTest(entity=entity, action=action):
                    self.assertTrue(name.startswith("api_fhir_r4."))

    def test_unknown_entity_or_action_raises(self):
        with self.assertRaises(KeyError):
            perms("nosuchentity", "query")
        with self.assertRaises(KeyError):
            perms("subscription", "nosuchaction")
        with self.assertRaises(KeyError):
            django_perms("subscription", "nosuchaction")

    def test_configured_reads_the_configured_value_not_the_declared_default(self):
        original = ApiFhirConfig.fhir_sub_search_perms
        try:
            ApiFhirConfig.fhir_sub_search_perms = ["999999"]
            self.assertEqual(configured_perms("subscription", "query"), ["999999"])
            self.assertEqual(perms("subscription", "query"), ["158001"])
        finally:
            ApiFhirConfig.fhir_sub_search_perms = original

    def test_configured_returns_none_for_an_undeclared_action(self):
        """None means "no rule": the caller must fail closed."""
        self.assertIsNone(configured_perms("subscription", "nosuchaction"))

    def test_ids_match_permissions_map(self):
        """The assembly's rights map must carry the same integers."""
        mapping = _load_permissions_map()
        if mapping is None:
            self.skipTest("permissions_map.json not found in this assembly")
        for key, right_id in EXPECTED_MAP_ENTRIES.items():
            with self.subTest(key=key):
                self.assertEqual(str(mapping.get(key)), right_id)
        declared_ids = {
            str(right_id)
            for actions in DJANGO_PERMS.values()
            for _, right_id in actions.values()
        }
        self.assertEqual(set(EXPECTED_MAP_ENTRIES.values()), declared_ids)

    # --- the access point through the model -------------------------------
    def test_model_exposes_every_action_of_its_entity(self):
        for action in DJANGO_PERMS["subscription"]:
            with self.subTest(action=action):
                self.assertEqual(
                    Subscription.get_rights(action),
                    configured_perms("subscription", action),
                )
                self.assertTrue(Subscription.get_rights(action))

    def test_model_returns_none_for_an_undeclared_action(self):
        self.assertIsNone(Subscription.get_rights("nosuchaction"))

    def test_model_reads_the_configured_value_not_the_declared_default(self):
        original = ApiFhirConfig.fhir_sub_search_perms
        try:
            ApiFhirConfig.fhir_sub_search_perms = ["999999"]
            self.assertEqual(Subscription.get_rights("query"), ["999999"])
            self.assertEqual(perms("subscription", "query"), ["158001"])
        finally:
            ApiFhirConfig.fhir_sub_search_perms = original

    def test_notification_result_inherits_the_subscription_rights(self):
        """
        A notification exists only for a subscription and has no rights of its own:
        `scope_parent` walks the chain up to `Subscription.get_rights`.
        """
        from core.rights_scope import model_rights, scope_parent_of

        self.assertIs(scope_parent_of(SubscriptionNotificationResult), Subscription)
        for action in DJANGO_PERMS["subscription"]:
            with self.subTest(action=action):
                self.assertEqual(
                    model_rights(SubscriptionNotificationResult, action),
                    list(Subscription.get_rights(action)),
                )

    def test_permission_class_resolves_from_the_model(self):
        """The REST check must read the model, not the import-time snapshot."""
        from api_fhir_r4.permissions import FHIRApiSubscriptionPermissions

        permission = FHIRApiSubscriptionPermissions()
        self.assertIs(permission.rights_model, Subscription)
        for verb, action in (
            ("GET", "query"),
            ("POST", "create"),
            ("PUT", "update"),
            ("DELETE", "delete"),
        ):
            with self.subTest(verb=verb):
                self.assertEqual(
                    permission.get_required_permissions(verb, Subscription),
                    list(Subscription.get_rights(action)),
                )
