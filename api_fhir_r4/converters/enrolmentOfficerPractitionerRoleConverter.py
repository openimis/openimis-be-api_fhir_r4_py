from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter, EnrolmentOfficerPractitionerConverter, ReferenceConverterMixin
from api_fhir_r4.converters.healthFacilityOrganisationConverter import LocationConverter, PersonConverterMixin
from api_fhir_r4.utils import DbManagerUtils
from core.models import Officer
from django.utils.translation import gettext as _
from fhir.resources.extension import Extension
from fhir.resources.practitionerrole import PractitionerRole


class EnrolmentOfficerPractitionerRoleConverter(BaseFHIRConverter, PersonConverterMixin, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_officer, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_practitioner_role = PractitionerRole.construct()
        cls.build_fhir_pk(fhir_practitioner_role, imis_officer, reference_type)
        cls.build_fhir_identifiers(fhir_practitioner_role, imis_officer)
        cls.build_fhir_extension(fhir_practitioner_role, imis_officer, reference_type)
        cls.build_fhir_practitioner_reference(fhir_practitioner_role, imis_officer, reference_type)
        cls.build_fhir_location_references(fhir_practitioner_role, imis_officer, reference_type)
        cls.build_fhir_code(fhir_practitioner_role)
        cls.build_fhir_telecom(fhir_practitioner_role, imis_officer)
        return fhir_practitioner_role

    @classmethod
    def to_imis_obj(cls, fhir_practitioner_role, audit_user_id):
        errors = []
        fhir_practitioner_role = PractitionerRole(**fhir_practitioner_role)
        practitioner = fhir_practitioner_role.practitioner
        imis_officer = EnrolmentOfficerPractitionerConverter.get_imis_obj_by_fhir_reference(practitioner, errors)
        location_references = fhir_practitioner_role.location
        location = cls.get_location_by_reference(location_references, errors)
        substitution_officer = None
        if fhir_practitioner_role.extension and len(fhir_practitioner_role.extension) > 0:
            substitution_officer_reference = fhir_practitioner_role.extension[0].valueReference
            substitution_officer = EnrolmentOfficerPractitionerConverter.get_imis_obj_by_fhir_reference(
                substitution_officer_reference,
            )
        if not cls.valid_condition(imis_officer is None, "Practitioner doesn't exists", errors):
            imis_officer.location = location
            if substitution_officer:
                imis_officer.substitution_officer = substitution_officer
        cls.check_errors(errors)
        return imis_officer

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

    @classmethod
    def get_reference_obj_uuid(cls, imis_officer):
        return imis_officer.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_officer):
        return imis_officer.id

    @classmethod
    def get_reference_obj_code(cls, imis_officer):
        return imis_officer.code

    @classmethod
    def get_fhir_resource_type(cls):
        return PractitionerRole

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_officer_code = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Officer, code=imis_officer_code)

    @classmethod
    def build_fhir_extension(cls, fhir_practitioner_role, imis_officer, reference_type):
        if imis_officer.substitution_officer:
            extension = Extension.construct()
            extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/practitioner-role-substitution-reference"

            reference = EnrolmentOfficerPractitionerConverter.build_fhir_resource_reference(
                imis_officer.substitution_officer,
                reference_type=reference_type
            )
            extension.valueReference = reference
            fhir_practitioner_role.extension = [extension]

    @classmethod
    def build_fhir_identifiers(cls, fhir_practitioner_role, imis_officer):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_officer)
        fhir_practitioner_role.identifier = identifiers

    @classmethod
    def build_fhir_code_identifier(cls, identifiers, imis_officer):
        if imis_officer.code:
            identifier = cls.build_fhir_identifier(imis_officer.code,
                                                   R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                   R4IdentifierConfig.get_fhir_generic_type_code())
            identifiers.append(identifier)

    @classmethod
    def build_fhir_practitioner_reference(cls, fhir_practitioner_role, imis_officer, reference_type):
        fhir_practitioner_role.practitioner = EnrolmentOfficerPractitionerConverter\
            .build_fhir_resource_reference(imis_officer, reference_type=reference_type)

    @classmethod
    def build_fhir_location_references(cls, fhir_practitioner_role, imis_officer, reference_type):
        if imis_officer.location:
            reference = LocationConverter.build_fhir_resource_reference(
                imis_officer.location, reference_type=reference_type)
            fhir_practitioner_role.location = [reference]

    @classmethod
    def get_location_by_reference(cls, location_references, errors):
        location = None
        if location_references:
            loc = cls.get_first_location(location_references)
            location = LocationConverter.get_imis_obj_by_fhir_reference(loc, errors)
        return location

    @classmethod
    def get_first_location(cls, location_references):
        return location_references[0]

    @classmethod
    def build_fhir_code(cls, fhir_practitioner_role):
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/practitioner-qualification-type"
        fhir_practitioner_role.code = [cls.build_codeable_concept(
            system=system,
            code="EO",
            display=_("Enrolment Officer")
        )]

    @classmethod
    def build_fhir_telecom(cls, fhir_practitioner_role, imis_officer):
        fhir_practitioner_role.telecom = cls.build_fhir_telecom_for_person(
            phone=imis_officer.phone,
            email=imis_officer.email
        )
