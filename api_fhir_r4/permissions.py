from location.models import Location
from rest_framework import exceptions
from rest_framework.permissions import DjangoModelPermissions

from api_fhir_r4 import rights
from core.rights_scope import VERB_ACTIONS, model_rights

# A right no role can hold: -1 is not a valid right identifier, so `has_perms([-1])`
# is False for everybody (superusers and imis_admin bypass it, as they do for any
# right).
#
# To be used to say "this verb is not exposed". It is the opposite of [], which refuses
# nothing: `has_perms([])` returns True by construction, so an empty list **opens**
# access to everybody instead of closing it. The two look alike when read, hence the
# named constant rather than a bare -1.
DENY = [-1]


class FHIRApiPermissions(DjangoModelPermissions):
    """
    Resolves a request's required rights, preferring the model's own declaration.

    The `permissions_*` lists below are a snapshot: they are evaluated when this module
    is imported, from `api_fhir_r4.rights`, which is itself a snapshot of the `_perms`
    config. That works only because nothing imports this module until after every
    `AppConfig.ready()` has run - a fragile guarantee, and one that keeps FHIR's idea of
    a right separate from the one GraphQL reads.

    So the model is asked first. `Model.get_rights(action)` reads the config at call
    time and is the same definition the GraphQL side uses, which makes it a single
    place to maintain (and one that follows a `scope_parent` for sub-resources). The
    lists remain the fallback for resources whose model does not declare rights yet, so
    conversion can be model by model.

    `permission_overrides` is for the cases where the REST path's real check genuinely
    differs from the model's canonical action - it must be documented where it is set,
    because it is a deliberate divergence rather than an oversight.
    """

    # Closed defaults: a subclass that forgets a verb refuses it instead of opening it
    # to everybody. The resources whose read is deliberately public (OMT-281
    # exemption) explicitly redeclare [] - which is then a readable decision, and not
    # an oversight.
    permissions_get = DENY
    permissions_post = DENY
    permissions_put = DENY
    permissions_patch = DENY
    permissions_delete = DENY
    base_class = None

    # The model whose `get_rights` governs this resource. Opt-in, and deliberately
    # NOT defaulted to the viewset's queryset model: the two are often different. The
    # CoverageEligibilityRequest viewset, for instance, has `queryset = Insuree...`
    # while the right it requires is the policy *eligibility* right - resolving from
    # the queryset model turned its POST into "create insuree" and locked out the very
    # users it is meant to serve. Each conversion is therefore explicit and reviewed.
    rights_model = None

    # verb -> right list, overriding both the model and the lists above.
    permission_overrides = {}

    def __init__(self):
        # Per-instance copy. `perms_map` is a class attribute on DRF's
        # DjangoModelPermissions, so the assignments below were mutating the *one* dict
        # shared by every permission class in the process: instantiating the Location
        # permissions - whose GET is deliberately empty, the OMT-281 open read - reset
        # every other resource's GET requirement to [], which `has_perms` grants to
        # everyone. DRF builds permission objects per request, so which rights applied
        # depended on the order requests happened to arrive in.
        self.perms_map = dict(self.perms_map)
        self.perms_map["GET"] = self.permissions_get
        self.perms_map["POST"] = self.permissions_post
        self.perms_map["PUT"] = self.permissions_put
        self.perms_map["PATCH"] = self.permissions_patch
        self.perms_map["DELETE"] = self.permissions_delete

    def get_required_permissions(self, method, model_cls):
        if method not in self.perms_map:
            raise exceptions.MethodNotAllowed(method)

        if method in self.permission_overrides:
            return list(self.permission_overrides[method])

        action = VERB_ACTIONS.get(method)
        if self.rights_model is not None and action is not None:
            declared = model_rights(self.rights_model, action)
            if declared is not None:
                return declared

        return self.perms_map[method]


class FHIRApiClaimPermissions(FHIRApiPermissions):
    # Rights come from Claim.get_rights, except POST (see permission_overrides).
    @property
    def rights_model(self):
        from claim.models import Claim

        return Claim

    permissions_get = rights.CLAIM_VIEW
    permissions_put = rights.CLAIM_CHANGE
    permissions_patch = rights.CLAIM_CHANGE
    permissions_delete = rights.CLAIM_DELETE

    @property
    def permission_overrides(self):
        # POST really does accept either right: serializers/claimSerializer.py
        # ::_create_claim_from_validated_data checks create OR submit, unlike GraphQL's
        # CreateClaimMutation which checks create alone. That is why it is an override
        # here instead of widening Claim.get_rights("create") for every API.
        #
        # It must be a flat list. This was `(rights.CLAIM_ADD, rights.CLAIM_SUBMIT)` -
        # a tuple of two *lists* - and `has_perms` compares each element against a
        # right id with `str(right) == str(perm)`, so "['111002']" never matched
        # anything and Claim POST was refused to every non-superuser.
        return {"POST": list(rights.CLAIM_ADD) + list(rights.CLAIM_SUBMIT)}


class FHIRApiCommunicationRequestPermissions(FHIRApiPermissions):
    permissions_get = rights.CLAIM_FEEDBACK_VIEW
    permissions_post = rights.CLAIM_FEEDBACK_DELIVER
    permissions_put = rights.CLAIM_FEEDBACK_DELIVER
    permissions_patch = rights.CLAIM_FEEDBACK_DELIVER
    permissions_delete = rights.CLAIM_FEEDBACK_SKIP


class FHIRApiPractitionerClaimAdminPermissions(FHIRApiPermissions):
    permissions_get = rights.CLAIM_ADMINISTRATOR_VIEW
    permissions_post = rights.CLAIM_ADMINISTRATOR_ADD
    permissions_put = rights.CLAIM_ADMINISTRATOR_CHANGE
    permissions_patch = rights.CLAIM_ADMINISTRATOR_CHANGE
    permissions_delete = rights.CLAIM_ADMINISTRATOR_DELETE


class FHIRApiPractitionerOfficerPermissions(FHIRApiPermissions):
    permissions_get = rights.ENROLMENT_OFFICER_VIEW
    permissions_post = rights.ENROLMENT_OFFICER_ADD
    permissions_put = rights.ENROLMENT_OFFICER_CHANGE
    permissions_patch = rights.ENROLMENT_OFFICER_CHANGE
    permissions_delete = rights.ENROLMENT_OFFICER_DELETE


class FHIRApiCoverageEligibilityRequestPermissions(FHIRApiPermissions):
    # POST performs the same eligibility lookup as GET, so it must require the same permission.
    permissions_get = rights.POLICY_ELIGIBILITY_VIEW
    permissions_post = rights.POLICY_ELIGIBILITY_VIEW
    #permissions_put = []
    #permissions_patch = []
    #permissions_delete = []


class FHIRApiCoverageRequestPermissions(FHIRApiPermissions):
    permissions_get = rights.POLICY_VIEW
    permissions_post = rights.POLICY_ADD
    permissions_put = rights.POLICY_CHANGE
    permissions_patch = rights.POLICY_CHANGE
    permissions_delete = rights.POLICY_DELETE


class FHIRApiLocationPermissions(FHIRApiPermissions):
    base_class = Location
    permissions_get = []
    permissions_post = rights.LOCATION_ADD
    permissions_put = rights.LOCATION_CHANGE
    permissions_patch = rights.LOCATION_CHANGE
    permissions_delete = rights.LOCATION_DELETE


class FHIRApiInsuranceOrganizationPermissions(FHIRApiPermissions):
    # InsuranceOrganizationSerializer.create()/update() are no-op stubs over static
    # module config data (not a mutable business record), and no destroy route exists
    # at all - there is no real mutation surface here to name a permission for.
    permissions_get = []
    #permissions_post = []
    #permissions_put = []
    #permissions_patch = []
    #permissions_delete = []


class FHIRApiInsureePermissions(FHIRApiPermissions):
    # Patient maps onto insuree.Insuree and its rights are that model's CRUD rights.
    @property
    def rights_model(self):
        from insuree.models import Insuree

        return Insuree

    permissions_get = rights.INSUREE_VIEW
    permissions_post = rights.INSUREE_ADD
    permissions_put = rights.INSUREE_CHANGE
    permissions_patch = rights.INSUREE_CHANGE
    permissions_delete = rights.INSUREE_DELETE


class FHIRApiMedicationPermissions(FHIRApiPermissions):
    permissions_get = []
    permissions_post = rights.MEDICAL_ITEM_ADD
    permissions_put = rights.MEDICAL_ITEM_CHANGE
    permissions_patch = rights.MEDICAL_ITEM_CHANGE
    permissions_delete = rights.MEDICAL_ITEM_DELETE


# No viewset uses it and no route exposes it. The closed values inherited from the
# base class make it harmless should it ever be wired up.
class FHIRApiConditionPermissions(FHIRApiPermissions):
    # Dead: no FHIR "Condition" resource (viewset/serializer/model) exists in this
    # module at all. This class is unused; kept only in case it's wired up later.
    permissions_get = []
    #permissions_post = []
    #permissions_put = []
    #permissions_patch = []
    #permissions_delete = []


class FHIRApiActivityDefinitionPermissions(FHIRApiPermissions):
    permissions_get = []
    permissions_post = rights.MEDICAL_SERVICE_ADD
    permissions_put = rights.MEDICAL_SERVICE_CHANGE
    permissions_patch = rights.MEDICAL_SERVICE_CHANGE
    permissions_delete = rights.MEDICAL_SERVICE_DELETE


class FHIRApiHealthServicePermissions(FHIRApiPermissions):
    permissions_get = []
    permissions_post = rights.HEALTH_FACILITY_ADD
    permissions_put = rights.HEALTH_FACILITY_CHANGE
    permissions_patch = rights.HEALTH_FACILITY_CHANGE
    permissions_delete = rights.HEALTH_FACILITY_DELETE


class FHIRApiGroupPermissions(FHIRApiPermissions):
    # Group maps onto insuree.Family and its rights are that model's CRUD rights - the
    # same four `insuree.apps` entries the `rights.FAMILY_*` aliases below name, read at
    # call time instead of snapshotted at import. The lists stay as the fallback.
    @property
    def rights_model(self):
        from insuree.models import Family

        return Family

    permissions_get = rights.FAMILY_VIEW
    permissions_post = rights.FAMILY_ADD
    permissions_put = rights.FAMILY_CHANGE
    permissions_patch = rights.FAMILY_CHANGE
    permissions_delete = rights.FAMILY_DELETE


class FHIRApiOrganizationPermissions(FHIRApiPermissions):
    permissions_get = rights.POLICY_HOLDER_VIEW
    permissions_post = rights.POLICY_HOLDER_ADD
    permissions_put = rights.POLICY_HOLDER_CHANGE
    permissions_patch = rights.POLICY_HOLDER_CHANGE
    permissions_delete = rights.POLICY_HOLDER_DELETE


class FHIRApiProductPermissions(FHIRApiPermissions):
    permissions_get = rights.PRODUCT_VIEW
    permissions_post = rights.PRODUCT_ADD
    permissions_put = rights.PRODUCT_CHANGE
    permissions_patch = rights.PRODUCT_CHANGE
    permissions_delete = rights.PRODUCT_DELETE


class FHIRApiInvoicePermissions(FHIRApiPermissions):
    permissions_get = rights.INVOICE_VIEW
    permissions_post = rights.INVOICE_ADD
    permissions_put = rights.INVOICE_CHANGE
    permissions_patch = rights.INVOICE_CHANGE
    permissions_delete = rights.INVOICE_DELETE


class FHIRApiBillPermissions(FHIRApiPermissions):
    permissions_get = rights.BILL_VIEW
    permissions_post = rights.BILL_ADD
    permissions_put = rights.BILL_CHANGE
    permissions_patch = rights.BILL_CHANGE
    permissions_delete = rights.BILL_DELETE


class FHIRApiPaymentPermissions(FHIRApiPermissions):
    permissions_get = rights.INVOICE_PAYMENT_VIEW
    permissions_post = rights.INVOICE_PAYMENT_ADD
    permissions_put = rights.INVOICE_PAYMENT_CHANGE
    permissions_patch = rights.INVOICE_PAYMENT_CHANGE
    permissions_delete = rights.INVOICE_PAYMENT_DELETE


class FHIRApiSubscriptionPermissions(FHIRApiPermissions):
    # The subscription is the only entity this module owns: its rights are declared in
    # `api_fhir_r4.apps.DJANGO_PERMS` and read by `Subscription.get_rights`, at check
    # time and not at import time.
    @property
    def rights_model(self):
        from api_fhir_r4.models import Subscription

        return Subscription

    permissions_get = rights.SUBSCRIPTION_VIEW
    permissions_post = rights.SUBSCRIPTION_ADD
    permissions_put = rights.SUBSCRIPTION_CHANGE
    permissions_patch = rights.SUBSCRIPTION_CHANGE
    permissions_delete = rights.SUBSCRIPTION_DELETE
