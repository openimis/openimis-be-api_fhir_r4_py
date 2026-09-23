"""
Garde-fous sur la declaration des droits d'api_fhir_r4.

Meme structure que `claim`, `core` ou `api_etl` : `DJANGO_PERMS` par entite puis par
action, `_PERM_CFG` qui en derive les cles de config, et `Subscription.get_rights` comme
point d'acces. La particularite de ce module est qu'il n'a presque pas de droits a lui :
sa couche REST/FHIR *emprunte* ceux des modules metier (`api_fhir_r4/rights.py`). Seule
la souscription FHIR lui appartient - un concept sans equivalent GraphQL, dont le modele
vit ici - et c'est la seule chose que `DJANGO_PERMS` doit declarer.

Ce qui est verrouille ici :
  * les identifiants 158001-158004, tels que deployes et tels que les porte
    `permissions_map.json` - en changer un retire l'acces aux roles qui le detiennent ;
  * le fait que `DJANGO_PERMS` **ne redeclare aucun droit emprunte** : un identifiant
    d'un autre module recopie ici serait une seconde definition, libre de diverger ;
  * une cle de config sans attribut de classe n'est jamais chargee et sa lecture leve
    AttributeError - le droit devient inapplicable ;
  * `has_perms([])` renvoie True, donc une liste vide accorde a tous.
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

# Les identifiants tels que deployes. En changer un est incompatible avec les roles
# existants : il faut mettre ce test a jour *et* accorder le nouveau droit.
EXPECTED_RIGHTS = {
    "fhir_sub_search_perms": ["158001"],
    "fhir_sub_create_perms": ["158002"],
    "fhir_sub_update_perms": ["158003"],
    "fhir_sub_delete_perms": ["158004"],
}

# Les cles de `permissions_map.json` qui portent ces memes identifiants.
EXPECTED_MAP_ENTRIES = {
    "api_fhir_r4.fhir_sub_search": "158001",
    "api_fhir_r4.fhir_sub_create": "158002",
    "api_fhir_r4.fhir_sub_update": "158003",
    "api_fhir_r4.fhir_sub_delete": "158004",
}


def _load_permissions_map():
    """`permissions_map.json` vit dans l'assemblage, pas dans le paquet."""
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
        Les droits sont des constantes posees depuis DJANGO_PERMS : l'attribut doit
        valoir la declaration, sans passer par la config.
        """
        for key, (entity, action) in _PERM_CFG.items():
            with self.subTest(key=key):
                self.assertEqual(getattr(ApiFhirConfig, key), perms(entity, action))

    # --- le module ne declare que ce qui lui appartient -------------------
    def test_only_the_subscription_entity_is_declared(self):
        """
        Les droits que la couche FHIR emprunte aux modules metier ne sont pas
        redeclares ici : leur source de verite est le `DJANGO_PERMS` du proprietaire,
        accessible par `Model.get_rights(action)`.
        """
        self.assertEqual(set(DJANGO_PERMS), {"subscription"})

    def test_every_declared_id_is_in_this_module_block(self):
        """158xxx est le bloc de ce module dans le catalogue openIMIS."""
        for entity, actions in DJANGO_PERMS.items():
            for action, (_, right_id) in actions.items():
                with self.subTest(entity=entity, action=action):
                    self.assertTrue(158000 <= right_id < 159000, right_id)

    def test_no_shared_right_ids(self):
        """Aucun partage d'identifiant n'est prevu dans ce module."""
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
        """L'app_label du modele Subscription dans cet assemblage est `api_fhir_r4`."""
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
        """None signifie "aucune regle" : l'appelant doit echouer ferme."""
        self.assertIsNone(configured_perms("subscription", "nosuchaction"))

    def test_ids_match_permissions_map(self):
        """La carte des droits de l'assemblage doit porter les memes entiers."""
        mapping = _load_permissions_map()
        if mapping is None:
            self.skipTest("permissions_map.json introuvable dans cet assemblage")
        for key, right_id in EXPECTED_MAP_ENTRIES.items():
            with self.subTest(key=key):
                self.assertEqual(str(mapping.get(key)), right_id)
        declared_ids = {
            str(right_id)
            for actions in DJANGO_PERMS.values()
            for _, right_id in actions.values()
        }
        self.assertEqual(set(EXPECTED_MAP_ENTRIES.values()), declared_ids)

    # --- le point d'acces par le modele -----------------------------------
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
        Une notification n'existe que pour une souscription et n'a pas de droits a elle :
        `scope_parent` remonte la chaine jusqu'a `Subscription.get_rights`.
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
        """Le controle REST doit lire le modele, pas l'instantane d'import."""
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
