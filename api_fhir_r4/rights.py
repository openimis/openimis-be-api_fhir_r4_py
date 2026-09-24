"""
Named permission constants for the FHIR R4 API (see `api_fhir_r4.permissions`).

**This file declares no right.** With one exception (the FHIR subscription, at the end
of the file), this module has no rights of its own: it *borrows* those of the business
modules. The source of truth of a borrowed right is the owning module's `DJANGO_PERMS`
- `claim.apps.DJANGO_PERMS`, `insuree.apps.DJANGO_PERMS`, etc. - and the canonical
access point is `Model.get_rights(action)`, which reads the *configured* value at check
time (see `core.rights_scope`). Redeclaring here an identifier belonging to another
module would make it a second definition, free to diverge silently.

Each constant below is therefore an ALIAS of the identifier list the owning module's
config class already exposes (e.g. `PolicyConfig.gql_mutation_create_policies_perms`),
never a hard-coded integer.

Two limits, owned:

  * an alias is a **snapshot taken at import time**. That only holds because nothing
    imports this module before every `AppConfig.ready()` has run. The snapshot-free
    form is `rights_model` in `api_fhir_r4/permissions.py`, which calls
    `Model.get_rights(action)` on every check; the constants here remain the fallback
    for the models that do not declare their rights yet (today: all of them except
    claim.Claim, insuree.Insuree, insuree.Family and api_fhir_r4.Subscription).
  * an owning module converted to `DJANGO_PERMS` does not necessarily expose one entity
    per FHIR resource: as long as there is no `get_rights` on the model concerned, the
    alias through the `_perms` key stays the only way to name the right.

Names follow Django's built-in permission-codename convention
(`view`/`add`/`change`/`delete` per model, i.e. `"<app_label>.<action>_<model>"`,
e.g. `"policy.add_policy"`) so this mapping is a mechanical one-to-one
substitution point if/when openIMIS migrates from its own right-ID system to
Django's built-in permissions: today
`POLICY_ADD = PolicyConfig.gql_mutation_create_policies_perms`, tomorrow it
could become `POLICY_ADD = ["policy.add_policy"]` without any other file
needing to change.

Every value here was verified against the real enforcement point for that
action (the serializer's underlying service call when one exists and checks
permissions itself, otherwise the equivalent GraphQL query/mutation) rather
than assigned by guessing from the Config attribute's name - see the inline
notes for anything non-obvious, dead/unreachable, or worth a maintainer's
attention.
"""
from api_fhir_r4.configurations import R4SubscriptionConfig
from claim.apps import ClaimConfig
from core.apps import CoreConfig
from insuree.apps import InsureeConfig
from invoice.apps import InvoiceConfig
from location.apps import LocationConfig
from medical.apps import MedicalConfig
from policy.apps import PolicyConfig
from policyholder.apps import PolicyholderConfig
from product.apps import ProductConfig


# --- claim.Claim ("claim.<action>_claim") -----------------------------------
# A borrowing: source of truth `claim.apps.DJANGO_PERMS`, entity "claim". The check
# goes through `Claim.get_rights(action)` (FHIRApiClaimPermissions.rights_model); these
# constants are now no more than the fallback and the readable name.
CLAIM_VIEW = ClaimConfig.gql_query_claims_perms
CLAIM_ADD = ClaimConfig.gql_mutation_create_claims_perms

CLAIM_SUBMIT = ClaimConfig.gql_mutation_submit_claims_perms
# The REST create path (serializers/claimSerializer.py::_create_claim_from_validated_data)
# checks create-OR-submit, unlike GraphQL's CreateClaimMutation which only checks create.
# Matching the real (broader) check the serializer performs, not just the mutation's name.
CLAIM_CHANGE = ClaimConfig.gql_mutation_update_claims_perms
# PUT/PATCH on Claim have no working serializer.update() (raises NotImplementedError) -
# this value is correct but currently unreachable in practice.
CLAIM_DELETE = ClaimConfig.gql_mutation_delete_claims_perms
# DELETE hard-deletes the row directly (Claim is a VersionedModel, not a HistoryModel, so
# the generic DestroyModelMixin skips any soft-delete/status workflow) - the permission id
# is correct, the underlying behaviour diverges from DeleteClaimsMutation's status workflow.

# --- claim.Feedback / Claim (feedback workflow) -----------------------------
CLAIM_FEEDBACK_VIEW = ClaimConfig.gql_query_claims_perms
# There is no dedicated "read feedback" right. The previous assignment here
# (gql_mutation_select_claim_feedback_perms) was a *mutation*-only right (used by
# SelectClaimsForFeedbackMutation to flip a status field) with no read role in the
# schema - the real analog for listing claims/feedback is the general claims-read right.
CLAIM_FEEDBACK_DELIVER = ClaimConfig.gql_mutation_deliver_claim_feedback_perms
CLAIM_FEEDBACK_SKIP = ClaimConfig.gql_mutation_skip_claim_feedback_perms
# DELETE (skip) hard-deletes the underlying Claim row instead of performing the
# non-destructive status flip SkipClaimsFeedbackMutation performs - id is correct,
# behaviour diverges.

# --- core.ClaimAdmin ("core.<action>_claimadministrator") -------------------
CLAIM_ADMINISTRATOR_VIEW = CoreConfig.gql_query_claim_administrator_perms
CLAIM_ADMINISTRATOR_ADD = CoreConfig.gql_mutation_create_claim_administrator_perms
CLAIM_ADMINISTRATOR_CHANGE = CoreConfig.gql_mutation_update_claim_administrator_perms
CLAIM_ADMINISTRATOR_DELETE = CoreConfig.gql_mutation_delete_claim_administrator_perms
# No GraphQL mutation currently uses these three rights: ClaimAdmin create/update/delete
# via GraphQL only happens as a side effect of the generic User CRUD mutations
# (CoreConfig.gql_mutation_create/update/delete_users_perms). These are dedicated,
# purpose-built rights instead (see permissions_map.json "core.claim_administrator"),
# kept as-is - whether they should instead be unified with the user-management rights is
# a product decision for an openIMIS maintainer, not something to change mechanically here.

# --- core.Officer ("core.<action>_enrolmentofficer") ------------------------
ENROLMENT_OFFICER_VIEW = CoreConfig.gql_query_enrolment_officers_perms
ENROLMENT_OFFICER_ADD = CoreConfig.gql_mutation_create_enrolment_officers_perms
ENROLMENT_OFFICER_CHANGE = CoreConfig.gql_mutation_update_enrolment_officers_perms
ENROLMENT_OFFICER_DELETE = CoreConfig.gql_mutation_delete_enrolment_officers_perms
# Same caveat as ClaimAdministrator above: ADD/CHANGE/DELETE are dedicated rights with no
# GraphQL mutation currently checking them (Officer CRUD in GraphQL goes through the
# generic User mutations instead). VIEW is genuinely shared with
# core.schema.resolve_enrolment_officers/resolve_substitution_enrolment_officers.

# --- policy.Policy, eligibility check ("policy.view_eligibility") ----------
POLICY_ELIGIBILITY_VIEW = PolicyConfig.gql_query_eligibilities_perms
# Used for both GET and POST /CoverageEligibilityRequest: POST runs the same real
# eligibility lookup GET would, so it must require the same permission. No service-layer
# check exists on this path (ByPolicyService has none) - this is the DRF class's sole gate.

# --- policy.Policy, Contract / Coverage ("policy.<action>_policy") ---------
POLICY_VIEW = PolicyConfig.gql_query_policies_perms
# Was PolicyConfig.gql_query_policies_by_insuree_perms. The REST queryset behind this
# (Policy.get_queryset(None, user)) lists ALL policies, not policies "by insuree" - the
# general query right is the conceptually correct one to alias. Both currently resolve to
# the same default right ID ("101201"), so this is a no-op today, but keeps the two from
# silently diverging if a deployment ever configures these rights differently.
POLICY_ADD = PolicyConfig.gql_mutation_create_policies_perms
POLICY_CHANGE = PolicyConfig.gql_mutation_edit_policies_perms
POLICY_DELETE = PolicyConfig.gql_mutation_delete_policies_perms
# None of PolicyService/ByPolicyService/the raw ORM calls the Contract/Coverage
# serializers use has any internal has_perms check - for POST/PUT/PATCH/DELETE these IDs
# are verified only against the analogous (but not always equivalent-in-behaviour)
# GraphQL mutation, not against a real service-layer check on this exact code path.

# --- location.Location ("location.<action>_location") ----------------------
LOCATION_ADD = LocationConfig.gql_mutation_create_locations_perms
LOCATION_CHANGE = LocationConfig.gql_mutation_edit_locations_perms
# Unlike GraphQL's UpdateLocationMutation (which additionally requires
# gql_mutation_create_region_locations_perms to touch Region/District rows, via
# LocationService._check_users_locations_rights), this REST path writes directly to the
# model and never calls LocationService - a real REST-vs-GraphQL authorization gap for
# Region/District locations, not fixable by changing which right is named here.
LOCATION_DELETE = LocationConfig.gql_mutation_delete_locations_perms

# --- location.HealthFacility ("location.<action>_healthfacility") ----------
HEALTH_FACILITY_ADD = LocationConfig.gql_mutation_create_health_facilities_perms
HEALTH_FACILITY_CHANGE = LocationConfig.gql_mutation_edit_health_facilities_perms
HEALTH_FACILITY_DELETE = LocationConfig.gql_mutation_delete_health_facilities_perms
# GET intentionally has no permission requirement (see FHIRApiHealthServicePermissions) -
# health facility listing is treated as open reference data, matching
# location.schema.resolve_health_facilities (permission check deliberately commented out,
# "OMT-281 allow anyone to query, limited by the get_queryset").

# --- insuree.Insuree / Patient ("insuree.<action>_insuree") -----------------
# A borrowing: source of truth `insuree.apps.DJANGO_PERMS`, entity "insuree". The
# check goes through `Insuree.get_rights(action)`
# (FHIRApiInsureePermissions.rights_model).
INSUREE_VIEW = InsureeConfig.gql_query_insurees_perms
INSUREE_ADD = InsureeConfig.gql_mutation_create_insurees_perms
INSUREE_CHANGE = InsureeConfig.gql_mutation_update_insurees_perms
# The equivalent GraphQL UpdateInsureeMutation actually checks
# gql_mutation_create_insurees_perms (insuree/gql_mutations.py) - almost certainly a bug
# there, not something to replicate here. Kept as the semantically-correct "update" right;
# flagging both places for a maintainer rather than silently matching the apparent bug.
INSUREE_DELETE = InsureeConfig.gql_mutation_delete_insurees_perms

# --- insuree.Family / Group ("insuree.<action>_family") ---------------------
# A borrowing: source of truth `insuree.apps.DJANGO_PERMS`, entity "family". The check
# goes through `Family.get_rights(action)` (FHIRApiGroupPermissions.rights_model).
FAMILY_VIEW = InsureeConfig.gql_query_families_perms
FAMILY_ADD = InsureeConfig.gql_mutation_create_families_perms
FAMILY_CHANGE = InsureeConfig.gql_mutation_update_families_perms
FAMILY_DELETE = InsureeConfig.gql_mutation_delete_families_perms
# Group POST/PUT also upsert non-head member Insuree records (GroupSerializer loops over
# members_family and calls InsureeService.create_or_update for each), gated only on this
# Family permission - GraphQL's closest analog (ChangeInsureeFamilyMutation) requires an
# Insuree permission too for that kind of change. Known enforcement gap, not fixed here
# (would require changing GroupSerializer's behaviour, not just which right is named).

# --- medical.Item / Medication ("medical.<action>_item") --------------------
MEDICAL_ITEM_ADD = MedicalConfig.gql_mutation_medical_items_add_perms
MEDICAL_ITEM_CHANGE = MedicalConfig.gql_mutation_medical_items_update_perms
MEDICAL_ITEM_DELETE = MedicalConfig.gql_mutation_medical_items_delete_perms
# GET intentionally has no permission requirement (OMT-281): medical items are treated as
# open reference data, mirroring medical.schema.resolve_medical_items / Item.get_queryset.

# --- medical.Service / ActivityDefinition ("medical.<action>_service") ------
MEDICAL_SERVICE_ADD = MedicalConfig.gql_mutation_medical_services_add_perms
MEDICAL_SERVICE_CHANGE = MedicalConfig.gql_mutation_medical_services_update_perms
MEDICAL_SERVICE_DELETE = MedicalConfig.gql_mutation_medical_services_delete_perms
# All three are currently unreachable: ActivityDefinitionViewSet only implements
# list/retrieve, no create/update/destroy route is registered. IDs match the analogous
# GraphQL mutations regardless, in case routes are added later.
# GET intentionally open, same OMT-281 rationale as Item above.

# --- policyholder.PolicyHolder / Organization ("policyholder.<action>_policyholder")
POLICY_HOLDER_VIEW = PolicyholderConfig.gql_query_policyholder_perms
POLICY_HOLDER_ADD = PolicyholderConfig.gql_mutation_create_policyholder_perms
POLICY_HOLDER_CHANGE = PolicyholderConfig.gql_mutation_update_policyholder_perms
POLICY_HOLDER_DELETE = PolicyholderConfig.gql_mutation_delete_policyholder_perms

# --- product.Product / InsurancePlan ("product.<action>_product") -----------
PRODUCT_VIEW = ProductConfig.gql_query_products_perms
# Was `[]`. Unlike medical Item/Service, Product has no OMT-281-style open-read carve-out
# anywhere else (no get_queryset exemption on the Product model, and GraphQL's
# resolve_products enforces this same right) - the previous empty list looks like a
# genuine oversight rather than an intentional design choice.
PRODUCT_ADD = ProductConfig.gql_mutation_products_add_perms
PRODUCT_CHANGE = ProductConfig.gql_mutation_products_edit_perms
PRODUCT_DELETE = ProductConfig.gql_mutation_products_delete_perms
# All three are currently unreachable: ProductViewSet is a ReadOnlyModelViewSet.

# --- invoice.Invoice ("invoice.<action>_invoice") ---------------------------
INVOICE_VIEW = InvoiceConfig.gql_invoice_search_perms
INVOICE_ADD = InvoiceConfig.gql_invoice_create_perms
# Moot: InvoiceSerializer.create() is a no-op `pass` stub, and no CreateInvoiceMutation
# exists to verify against (only a bulk GenerateTimeframeInvoices mutation does, which
# isn't equivalent) - naming-consistent guess only.
INVOICE_CHANGE = InvoiceConfig.gql_invoice_update_perms
# Moot: InvoiceSerializer.update() is a no-op `pass` stub, and no UpdateInvoiceMutation
# exists anywhere in the codebase to verify against - naming-consistent guess only.
INVOICE_DELETE = InvoiceConfig.gql_invoice_delete_perms
# Unreachable: InvoiceViewSet has no destroy route (MultiSerializerModelViewSet doesn't
# mix in a Destroy mixin, and the viewset defines no destroy() of its own).

# --- invoice.Bill ("invoice.<action>_bill") ---------------------------------
BILL_VIEW = InvoiceConfig.gql_bill_search_perms
BILL_ADD = InvoiceConfig.gql_bill_create_perms
# Moot: BillSerializer.create() is a no-op `pass` stub; no CreateBillMutation exists.
BILL_CHANGE = InvoiceConfig.gql_bill_update_perms
# Moot: BillSerializer.update() is a no-op `pass` stub; no UpdateBillMutation exists.
BILL_DELETE = InvoiceConfig.gql_bill_delete_perms
# Unreachable, same reason as INVOICE_DELETE above (shared viewset).

# --- invoice.PaymentInvoice / PaymentNotice ("invoice.<action>_paymentinvoice")
INVOICE_PAYMENT_VIEW = InvoiceConfig.gql_invoice_payment_search_perms
INVOICE_PAYMENT_ADD = InvoiceConfig.gql_invoice_payment_create_perms
INVOICE_PAYMENT_CHANGE = InvoiceConfig.gql_invoice_payment_update_perms
# Moot: PaymentNoticeSerializer.update() is a no-op `pass` stub.
INVOICE_PAYMENT_DELETE = InvoiceConfig.gql_invoice_payment_delete_perms
# This is the one Invoice-family resource where every verb is actually reachable and,
# for GET/POST/DELETE, backed by a real service call - PaymentNoticeViewSet is a plain
# ModelViewSet (unlike Invoice/Bill's multiserializer viewset), so DELETE is routed.

# --- api_fhir_r4.Subscription ("api_fhir_r4.<action>_subscription") --------
# The only entity this module owns. Its source of truth is now
# `api_fhir_r4.apps.DJANGO_PERMS` (entity "subscription", identifiers 158001-158004)
# and the check goes through `Subscription.get_rights(action)`
# (FHIRApiSubscriptionPermissions.rights_model). The constants below remain aliases of
# the same values, through the AppConfig's constants.
SUBSCRIPTION_VIEW = R4SubscriptionConfig.get_fhir_sub_search_perms()
SUBSCRIPTION_ADD = R4SubscriptionConfig.get_fhir_sub_create_perms()
SUBSCRIPTION_CHANGE = R4SubscriptionConfig.get_fhir_sub_update_perms()
SUBSCRIPTION_DELETE = R4SubscriptionConfig.get_fhir_sub_delete_perms()
# Subscription is a FHIR-only concept (no core GraphQL equivalent) whose model and
# rights live entirely in this module - unlike every other constant above, there is no
# other module to borrow from. SubscriptionSerializer additionally layers on two
# independent checks on top of this (not a substitute for it): the requester must also
# hold the read permission for whatever resource type they're subscribing to
# (check_resource_rights), and update/delete additionally require being the
# subscription's original creator (check_object_owner).
