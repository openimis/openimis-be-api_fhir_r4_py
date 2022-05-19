from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter, ClaimAdminPractitionerConverter, ReferenceConverterMixin
from api_fhir_r4.converters.healthFacilityOrganisationConverter import HealthFacilityOrganisationConverter, PersonConverterMixin
from api_fhir_r4.utils import DbManagerUtils
from claim.models import ClaimAdmin
from django.utils.translation import gettext as _
from fhir.resources.practitionerrole import PractitionerRole


class ClaimAdminPractitionerRoleConverter(BaseFHIRConverter, PersonConverterMixin, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_claim_admin, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_practitioner_role = PractitionerRole.construct()
        cls.build_fhir_pk(fhir_practitioner_role, imis_claim_admin, reference_type)
        cls.build_fhir_identifiers(fhir_practitioner_role, imis_claim_admin)
        cls.build_fhir_practitioner_reference(fhir_practitioner_role, imis_claim_admin, reference_type)
        cls.build_fhir_healthcare_service_references(fhir_practitioner_role, imis_claim_admin, reference_type)
        cls.build_fhir_code(fhir_practitioner_role)
        cls.build_fhir_telecom(fhir_practitioner_role, imis_claim_admin)
        return fhir_practitioner_role

    @classmethod
    def to_imis_obj(cls, fhir_practitioner_role, audit_user_id):
        errors = []
        fhir_practitioner_role = PractitionerRole(**fhir_practitioner_role)
        practitioner = fhir_practitioner_role.practitioner
        claim_admin = ClaimAdminPractitionerConverter.get_imis_obj_by_fhir_reference(practitioner, errors)
        hf_references = fhir_practitioner_role.organization
        health_facility = cls.get_healthcare_service_by_reference(hf_references, errors)

        if not cls.valid_condition(claim_admin is None, "Practitioner doesn't exists", errors):
            claim_admin.health_facility = health_facility
        cls.check_errors(errors)
        return claim_admin

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

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
    def build_fhir_code_identifier(cls, identifiers, imis_claim_admin):
        if imis_claim_admin.code:
            identifier = cls.build_fhir_identifier(imis_claim_admin.code,
                                                   R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                   R4IdentifierConfig.get_fhir_generic_type_code())
            identifiers.append(identifier)

    @classmethod
    def build_fhir_practitioner_reference(cls, fhir_practitioner_role, imis_claim_admin, reference_type):
        fhir_practitioner_role.practitioner = ClaimAdminPractitionerConverter\
            .build_fhir_resource_reference(imis_claim_admin, reference_type=reference_type)

    @classmethod
    def build_fhir_healthcare_service_references(cls, fhir_practitioner_role, imis_claim_admin, reference_type):
        if imis_claim_admin.health_facility:
            reference = HealthFacilityOrganisationConverter.build_fhir_resource_reference(
                imis_claim_admin.health_facility, 'Organization', reference_type=reference_type)
            fhir_practitioner_role.organization = reference

    @classmethod
    def get_healthcare_service_by_reference(cls, organization_references, errors):
        health_facility = None
        if organization_references:
            location = cls.get_first_location(organization_references)
            health_facility = HealthFacilityOrganisationConverter.get_imis_obj_by_fhir_reference(location, errors)
        return health_facility

    @classmethod
    def get_first_location(cls, location_references):
        return location_references

    @classmethod
    def build_fhir_code(cls, fhir_practitioner_role):
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/practitioner-qualification-type"
        fhir_practitioner_role.code = [cls.build_codeable_concept(
            system=system,
            code="CA",
            display=_("Claim Administrator")
        )]

    @classmethod
    def build_fhir_telecom(cls, fhir_practitioner_role, imis_claim_admin):
        fhir_practitioner_role.telecom = cls.build_fhir_telecom_for_person(
            phone=imis_claim_admin.phone,
            email=imis_claim_admin.email_id
        )
