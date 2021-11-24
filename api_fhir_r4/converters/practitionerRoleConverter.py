from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter, PractitionerConverter, ReferenceConverterMixin
from api_fhir_r4.converters.healthcareServiceConverter import HealthcareServiceConverter
from claim.models import ClaimAdmin
from fhir.resources.practitionerrole import PractitionerRole
from api_fhir_r4.utils import DbManagerUtils


class PractitionerRoleConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_claim_admin, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_practitioner_role = PractitionerRole.construct()
        cls.build_fhir_pk(fhir_practitioner_role, imis_claim_admin, reference_type)
        cls.build_fhir_identifiers(fhir_practitioner_role, imis_claim_admin)
        cls.build_fhir_practitioner_reference(fhir_practitioner_role, imis_claim_admin, reference_type)
        cls.build_fhir_healthcare_service_references(fhir_practitioner_role, imis_claim_admin, reference_type)
        return fhir_practitioner_role

    @classmethod
    def to_imis_obj(cls, fhir_practitioner_role, audit_user_id):
        errors = []
        fhir_practitioner_role = PractitionerRole(**fhir_practitioner_role)
        practitioner = fhir_practitioner_role.practitioner
        claim_admin = PractitionerConverter.get_imis_obj_by_fhir_reference(practitioner, errors)
        hf_references = fhir_practitioner_role.location
        health_facility = cls.get_healthcare_service_by_reference(hf_references, errors)

        if not cls.valid_condition(claim_admin is None, "Practitioner doesn't exists", errors):
            claim_admin.health_facility = health_facility
        cls.check_errors(errors)
        return claim_admin

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_claim_admin_code_type()

    @classmethod
    def get_reference_obj_uuid(cls, imis_obj):
        return imis_obj.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_obj):
        return imis_obj.id

    @classmethod
    def get_reference_obj_code(cls, imis_obj):
        return imis_obj.code

    @classmethod
    def get_fhir_resource_type(cls):
        return PractitionerRole

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_claim_admin_code = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(ClaimAdmin, code=imis_claim_admin_code)

    @classmethod
    def build_fhir_identifiers(cls, fhir_practitioner_role, imis_claim_admin):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_claim_admin)
        fhir_practitioner_role.identifier = identifiers

    @classmethod
    def build_fhir_practitioner_reference(cls, fhir_practitioner_role, imis_claim_admin, reference_type):
        fhir_practitioner_role.practitioner = PractitionerConverter\
            .build_fhir_resource_reference(imis_claim_admin, reference_type=reference_type)

    @classmethod
    def build_fhir_healthcare_service_references(cls, fhir_practitioner_role, imis_claim_admin, reference_type):
        if imis_claim_admin.health_facility:
            reference = HealthcareServiceConverter.build_fhir_resource_reference(
                imis_claim_admin.health_facility, reference_type=reference_type)
            fhir_practitioner_role.healthcareService = [reference]

    @classmethod
    def get_healthcare_service_by_reference(cls, location_references, errors):
        health_facility = None
        if location_references:
            location = cls.get_first_location(location_references)
            health_facility = HealthcareServiceConverter.get_imis_obj_by_fhir_reference(location, errors)
        return health_facility

    @classmethod
    def get_first_location(cls, location_references):
        return location_references[0]
