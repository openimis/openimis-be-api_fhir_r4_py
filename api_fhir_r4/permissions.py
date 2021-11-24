from claim.apps import ClaimConfig
from insuree.apps import InsureeConfig
from location.apps import LocationConfig
from policy.apps import PolicyConfig
from policyholder.apps import PolicyholderConfig
from medical.apps import MedicalConfig
from rest_framework import exceptions
from rest_framework.permissions import DjangoModelPermissions


class FHIRApiPermissions(DjangoModelPermissions):
    permissions_get = []
    permissions_post = []
    permissions_put = []
    permissions_patch = []
    permissions_delete = []

    def __init__(self):
        self.perms_map['GET'] = self.permissions_get
        self.perms_map['POST'] = self.permissions_post
        self.perms_map['PUT'] = self.permissions_put
        self.perms_map['PATCH'] = self.permissions_patch
        self.perms_map['DELETE'] = self.permissions_delete

    def get_required_permissions(self, method, model_cls):
        if method not in self.perms_map:
            raise exceptions.MethodNotAllowed(method)

        return self.perms_map[method]


class FHIRApiClaimPermissions(FHIRApiPermissions):
    permissions_get = ClaimConfig.gql_query_claims_perms
    permissions_post = ClaimConfig.gql_mutation_create_claims_perms
    permissions_put = ClaimConfig.gql_mutation_update_claims_perms
    permissions_patch = ClaimConfig.gql_mutation_update_claims_perms
    permissions_delete = ClaimConfig.gql_mutation_delete_claims_perms


class FHIRApiCommunicationRequestPermissions(FHIRApiPermissions):
    permissions_get = ClaimConfig.gql_mutation_select_claim_feedback_perms
    permissions_post = ClaimConfig.gql_mutation_deliver_claim_feedback_perms
    permissions_put = ClaimConfig.gql_mutation_deliver_claim_feedback_perms
    permissions_patch = ClaimConfig.gql_mutation_deliver_claim_feedback_perms
    permissions_delete = ClaimConfig.gql_mutation_skip_claim_feedback_perms


class FHIRApiPractitionerPermissions(FHIRApiPermissions):
    permissions_get = ClaimConfig.gql_query_claim_admins_perms
    permissions_post = ClaimConfig.gql_query_claim_admins_perms
    permissions_put = ClaimConfig.gql_query_claim_admins_perms
    permissions_patch = ClaimConfig.gql_query_claim_admins_perms
    permissions_delete = ClaimConfig.gql_query_claim_admins_perms


class FHIRApiCoverageEligibilityRequestPermissions(FHIRApiPermissions):
    permissions_get = PolicyConfig.gql_query_eligibilities_perms
    permissions_post = []
    permissions_put = []
    permissions_patch = []
    permissions_delete = []


class FHIRApiCoverageRequestPermissions(FHIRApiPermissions):
    permissions_get = PolicyConfig.gql_query_policies_by_insuree_perms
    permissions_post = []
    permissions_put = []
    permissions_patch = []
    permissions_delete = []


class FHIRApiHFPermissions(FHIRApiPermissions):
    permissions_get = LocationConfig.gql_query_health_facilities_perms
    permissions_post = LocationConfig.gql_mutation_create_health_facilities_perms
    permissions_put = LocationConfig.gql_mutation_create_health_facilities_perms
    permissions_patch = LocationConfig.gql_mutation_create_health_facilities_perms
    permissions_delete = LocationConfig.gql_mutation_delete_health_facilities_perms


class FHIRApiInsureePermissions(FHIRApiPermissions):
    permissions_get = InsureeConfig.gql_query_insurees_perms
    permissions_post = InsureeConfig.gql_mutation_create_insurees_perms
    permissions_put = InsureeConfig.gql_mutation_update_insurees_perms
    permissions_patch = InsureeConfig.gql_mutation_update_insurees_perms
    permissions_delete = InsureeConfig.gql_mutation_delete_insurees_perms


class FHIRApiMedicationPermissions(FHIRApiPermissions):
    permissions_get = MedicalConfig.gql_query_medical_items_perms
    permissions_post = MedicalConfig.gql_mutation_medical_items_add_perms
    permissions_put = MedicalConfig.gql_mutation_medical_items_update_perms
    permissions_patch = MedicalConfig.gql_mutation_medical_items_update_perms
    permissions_delete = MedicalConfig.gql_mutation_medical_items_delete_perms


class FHIRApiConditionPermissions(FHIRApiPermissions):
    permissions_get = MedicalConfig.gql_query_diagnosis_perms
    permissions_post = []
    permissions_put = []
    permissions_patch = []
    permissions_delete = []


class FHIRApiActivityDefinitionPermissions(FHIRApiPermissions):
    permissions_get = MedicalConfig.gql_query_medical_services_perms
    permissions_post = MedicalConfig.gql_mutation_medical_services_add_perms
    permissions_put = MedicalConfig.gql_mutation_medical_services_update_perms
    permissions_patch = MedicalConfig.gql_mutation_medical_services_update_perms
    permissions_delete = MedicalConfig.gql_mutation_medical_services_delete_perms


class FHIRApiHealthServicePermissions(FHIRApiPermissions):
    permissions_get = LocationConfig.gql_query_health_facilities_perms
    permissions_post = LocationConfig.gql_mutation_create_health_facilities_perms
    permissions_put = LocationConfig.gql_mutation_edit_health_facilities_perms
    permissions_patch = LocationConfig.gql_mutation_edit_health_facilities_perms
    permissions_delete = LocationConfig.gql_mutation_delete_health_facilities_perms


class FHIRApiGroupPermissions(FHIRApiPermissions):
    permissions_get = InsureeConfig.gql_query_families_perms
    permissions_post = InsureeConfig.gql_mutation_create_families_perms
    permissions_put = InsureeConfig.gql_mutation_update_families_perms
    permissions_patch = InsureeConfig.gql_mutation_update_families_perms
    permissions_delete = InsureeConfig.gql_mutation_delete_families_perms


class FHIRApiOrganizationPermissions(FHIRApiPermissions):
    permissions_get = PolicyholderConfig.gql_query_policyholder_perms
    permissions_post = PolicyholderConfig.gql_mutation_create_policyholder_perms
    permissions_put = PolicyholderConfig.gql_mutation_update_policyholder_perms
    permissions_patch = PolicyholderConfig.gql_mutation_update_policyholder_perms
    permissions_delete = PolicyholderConfig.gql_mutation_delete_policyholder_perms
