"""
FHIR resolves its rights from the model, like the rest of the stack.

`api_fhir_r4.rights` assigns config values at module import, so every `permissions_*`
list is a snapshot of a snapshot. It happens to hold today only because nothing imports
`permissions.py` until after every `AppConfig.ready()`, and it kept FHIR's idea of a
right separate from the one GraphQL reads. `Model.get_rights(action)` is read at call
time and shared by both, so the permission classes now ask the model first and keep the
lists only as a fallback for models that have not declared rights yet.

Three defects found while wiring this up are pinned here:

  * `perms_map` is a class attribute on DRF's DjangoModelPermissions, and the previous
    `__init__` mutated it in place - one dict shared by every permission class in the
    process. Instantiating the Location permissions, whose GET is deliberately empty,
    reset every other resource's GET to [], which `has_perms` grants to everyone. DRF
    builds permission objects per request, so authorisation depended on request order.
  * Claim POST was `(rights.CLAIM_ADD, rights.CLAIM_SUBMIT)` - a tuple of two *lists*.
    `has_perm` compares with `str(right) == str(perm)`, so "['111002']" matched nothing
    and POST was refused to every non-superuser.
  * Insuree PUT used to disagree with GraphQL, which checked the create right on update.
    Both now read `Insuree.get_rights("update")`.
"""

from django.test import TestCase
from rest_framework.permissions import DjangoModelPermissions

from api_fhir_r4 import rights
from api_fhir_r4.permissions import (
    DENY,
    FHIRApiPermissions,
    FHIRApiClaimPermissions,
    FHIRApiCoverageEligibilityRequestPermissions,
    FHIRApiInsureePermissions,
    FHIRApiLocationPermissions,
)
from claim.models import Claim
from insuree.models import Insuree


class FHIRPermissionAlignmentTestCase(TestCase):
    # --- resolution comes from the model ----------------------------------
    def test_insuree_verbs_resolve_from_the_model(self):
        permission = FHIRApiInsureePermissions()
        for verb, action in (
            ("GET", "query"),
            ("POST", "create"),
            ("PUT", "update"),
            ("PATCH", "update"),
            ("DELETE", "delete"),
        ):
            with self.subTest(verb=verb):
                self.assertEqual(
                    permission.get_required_permissions(verb, Insuree),
                    list(Insuree.get_rights(action)),
                )

    def test_insuree_update_is_the_update_right_not_create(self):
        permission = FHIRApiInsureePermissions()
        self.assertEqual(
            permission.get_required_permissions("PUT", Insuree),
            list(Insuree.get_rights("update")),
        )
        self.assertNotEqual(
            permission.get_required_permissions("PUT", Insuree),
            list(Insuree.get_rights("create")),
        )

    def test_resolution_tracks_a_config_change_without_reimport(self):
        """The point of asking the model: no snapshot to go stale."""
        from insuree.apps import InsureeConfig

        permission = FHIRApiInsureePermissions()
        original = InsureeConfig.gql_query_insurees_perms
        try:
            InsureeConfig.gql_query_insurees_perms = ["999999"]
            self.assertEqual(
                permission.get_required_permissions("GET", Insuree), ["999999"]
            )
        finally:
            InsureeConfig.gql_query_insurees_perms = original

    def test_group_verbs_resolve_from_the_family_model(self):
        """
        Group est insuree.Family : le droit vient du modele proprietaire, pas d'un
        instantane de `rights.FAMILY_*`. Les valeurs sont les memes - c'est le moment
        de la lecture qui change.
        """
        from api_fhir_r4.permissions import FHIRApiGroupPermissions
        from insuree.models import Family

        permission = FHIRApiGroupPermissions()
        self.assertIs(permission.rights_model, Family)
        for verb, action in (
            ("GET", "query"),
            ("POST", "create"),
            ("PUT", "update"),
            ("PATCH", "update"),
            ("DELETE", "delete"),
        ):
            with self.subTest(verb=verb):
                self.assertEqual(
                    permission.get_required_permissions(verb, Family),
                    list(Family.get_rights(action)),
                )

    def test_group_resolution_matches_the_previous_snapshot(self):
        """Le passage au modele ne change aucune valeur exigee aujourd'hui."""
        from api_fhir_r4.permissions import FHIRApiGroupPermissions
        from insuree.models import Family

        permission = FHIRApiGroupPermissions()
        for verb, expected in (
            ("GET", rights.FAMILY_VIEW),
            ("POST", rights.FAMILY_ADD),
            ("PUT", rights.FAMILY_CHANGE),
            ("PATCH", rights.FAMILY_CHANGE),
            ("DELETE", rights.FAMILY_DELETE),
        ):
            with self.subTest(verb=verb):
                self.assertEqual(
                    permission.get_required_permissions(verb, Family), list(expected)
                )

    # --- the documented override ------------------------------------------
    def test_claim_post_accepts_create_or_submit_as_a_flat_list(self):
        permission = FHIRApiClaimPermissions()
        required = permission.get_required_permissions("POST", Claim)
        self.assertEqual(
            required, list(rights.CLAIM_ADD) + list(rights.CLAIM_SUBMIT)
        )
        self.assertTrue(
            all(isinstance(r, str) for r in required),
            f"every entry must be a right id, got {required}",
        )

    def test_claim_other_verbs_still_come_from_the_model(self):
        permission = FHIRApiClaimPermissions()
        self.assertEqual(
            permission.get_required_permissions("GET", Claim),
            list(Claim.get_rights("query")),
        )
        self.assertEqual(
            permission.get_required_permissions("DELETE", Claim),
            list(Claim.get_rights("delete")),
        )

    # --- the shared-dict defect -------------------------------------------
    def test_perms_map_is_not_shared_between_permission_classes(self):
        insuree = FHIRApiInsureePermissions()
        before = list(insuree.perms_map["GET"])
        FHIRApiLocationPermissions()  # its GET is deliberately empty
        self.assertEqual(
            insuree.perms_map["GET"],
            before,
            "instantiating another permission class must not alter this one",
        )

    def test_perms_map_is_not_the_drf_class_attribute(self):
        insuree = FHIRApiInsureePermissions()
        self.assertIsNot(insuree.perms_map, DjangoModelPermissions.perms_map)

    def test_an_empty_resource_does_not_leak_into_another(self):
        """
        The concrete failure: Location GET is empty on purpose, and used to blank out
        Insuree's GET requirement for whatever request came next.
        """
        FHIRApiLocationPermissions()
        insuree = FHIRApiInsureePermissions()
        self.assertEqual(
            insuree.get_required_permissions("GET", Insuree),
            list(Insuree.get_rights("query")),
        )
        self.assertTrue(insuree.get_required_permissions("GET", Insuree))

    # --- resolution is opt-in, and has to be ------------------------------
    def test_resolution_is_opt_in_per_resource(self):
        """
        A viewset's queryset model is often not the model whose rights apply, so the
        model is only consulted when a permission class names it.
        """
        self.assertIsNone(FHIRApiLocationPermissions().rights_model)
        self.assertIs(FHIRApiInsureePermissions().rights_model, Insuree)
        self.assertIs(FHIRApiClaimPermissions().rights_model, Claim)

    def test_coverage_eligibility_keeps_its_own_right(self):
        """
        Its viewset has `queryset = Insuree...`, but the right it requires is the
        policy eligibility right. Resolving from the queryset model turned POST into
        "create insuree" and denied the users it exists for.
        """
        permission = FHIRApiCoverageEligibilityRequestPermissions()
        self.assertIsNone(permission.rights_model)
        for verb in ("GET", "POST"):
            with self.subTest(verb=verb):
                self.assertEqual(
                    permission.get_required_permissions(verb, Insuree),
                    list(rights.POLICY_ELIGIBILITY_VIEW),
                )
                self.assertNotEqual(
                    permission.get_required_permissions(verb, Insuree),
                    list(Insuree.get_rights("create")),
                )


class DenySentinelTestCase(TestCase):
    """
    `DENY` ([-1]) refuse, `[]` autorise - et les deux se ressemblent a la lecture.

    `has_perms([])` renvoie True par construction (core.models.user.User.has_perms), donc
    une liste vide **ouvre** un verbe au lieu de le fermer. -1 n'etant pas un identifiant
    de droit valide, aucun role ne peut le detenir : c'est la maniere d'ecrire "ce verbe
    n'est pas expose". Les superusers et imis_admin passent outre, comme pour tout droit.
    """

    def test_deny_is_refused_and_empty_is_granted(self):
        from core.test_helpers import create_right_only_user

        user = create_right_only_user("fhir_deny_probe", ["gql_query_users_perms"])
        self.assertFalse(user.has_perms(DENY), "DENY doit refuser")
        self.assertTrue(user.has_perms([]), "[] autorise tout le monde, par construction")

    def test_base_class_defaults_are_closed(self):
        """
        Une sous-classe qui oublie un verbe doit le refuser, pas l'ouvrir a tous.
        """
        for verb in ("get", "post", "put", "patch", "delete"):
            with self.subTest(verb=verb):
                self.assertEqual(getattr(FHIRApiPermissions, f"permissions_{verb}"), DENY)

    def test_open_reads_stay_explicitly_open(self):
        """
        L'exemption OMT-281 : ces lectures sont volontairement publiques et doivent le
        redeclarer explicitement, sinon elles heriteraient du refus.
        """
        from api_fhir_r4.permissions import (
            FHIRApiActivityDefinitionPermissions,
            FHIRApiHealthServicePermissions,
            FHIRApiMedicationPermissions,
        )

        for cls in (
            FHIRApiLocationPermissions,
            FHIRApiMedicationPermissions,
            FHIRApiActivityDefinitionPermissions,
            FHIRApiHealthServicePermissions,
        ):
            with self.subTest(cls=cls.__name__):
                self.assertEqual(cls.permissions_get, [])

    def test_multiserializer_views_only_require_authentication(self):
        """
        Le droit reel vient du tuple de chaque serializer enregistre. L'attribut de
        classe declare ici masquait la propriete du mixin, si bien que ces vues
        s'appuyaient sur FHIRApiPermissions et ses listes vides.
        """
        from rest_framework.permissions import IsAuthenticated

        from api_fhir_r4.views.fhir.base import BaseMultiserializerFHIRView

        self.assertEqual(
            BaseMultiserializerFHIRView.permission_classes, (IsAuthenticated,)
        )
