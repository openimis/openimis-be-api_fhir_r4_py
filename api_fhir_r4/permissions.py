from location.models import Location
from rest_framework import exceptions
from rest_framework.permissions import DjangoModelPermissions

from api_fhir_r4 import rights


class FHIRApiPermissions(DjangoModelPermissions):
    permissions_get = []
    permissions_post = []
    permissions_put = []
    permissions_patch = []
    permissions_delete = []
    base_class = None

    def __init__(self):
        self.perms_map["GET"] = self.permissions_get
        self.perms_map["POST"] = self.permissions_post
        self.perms_map["PUT"] = self.permissions_put
        self.perms_map["PATCH"] = self.permissions_patch
        self.perms_map["DELETE"] = self.permissions_delete

    def get_required_permissions(self, method, model_cls):
        if method not in self.perms_map:
            raise exceptions.MethodNotAllowed(method)

        return self.perms_map[method]


class FHIRApiClaimPermissions(FHIRApiPermissions):
    permissions_get = rights.CLAIM_VIEW
    permissions_post = (rights.CLAIM_ADD, rights.CLAIM_SUBMIT)
    permissions_put = rights.CLAIM_CHANGE
    permissions_patch = rights.CLAIM_CHANGE
    permissions_delete = rights.CLAIM_DELETE


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
    permissions_put = []
    permissions_patch = []
    permissions_delete = []


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
    permissions_post = []
    permissions_put = []
    permissions_patch = []
    permissions_delete = []


class FHIRApiInsureePermissions(FHIRApiPermissions):
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


class FHIRApiConditionPermissions(FHIRApiPermissions):
    # Dead: no FHIR "Condition" resource (viewset/serializer/model) exists in this
    # module at all. This class is unused; kept only in case it's wired up later.
    permissions_get = []
    permissions_post = []
    permissions_put = []
    permissions_patch = []
    permissions_delete = []


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
    permissions_get = rights.SUBSCRIPTION_VIEW
    permissions_post = rights.SUBSCRIPTION_ADD
    permissions_put = rights.SUBSCRIPTION_CHANGE
    permissions_patch = rights.SUBSCRIPTION_CHANGE
    permissions_delete = rights.SUBSCRIPTION_DELETE
