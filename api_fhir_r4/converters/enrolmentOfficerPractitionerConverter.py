from core.models import Officer
from django.utils.translation import gettext as _

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter, PersonConverterMixin, ReferenceConverterMixin
from fhir.resources.R4B.practitioner import Practitioner, PractitionerQualification
from api_fhir_r4.utils import TimeUtils, DbManagerUtils


class EnrolmentOfficerPractitionerConverter(BaseFHIRConverter, PersonConverterMixin, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_officer, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_practitioner = Practitioner.construct()
        cls.build_fhir_pk(fhir_practitioner, imis_officer, reference_type)
        cls.build_fhir_identifiers(fhir_practitioner, imis_officer)
        cls.build_human_names(fhir_practitioner, imis_officer)
        cls.build_fhir_birth_date(fhir_practitioner, imis_officer)
        cls.build_fhir_telecom(fhir_practitioner, imis_officer)
        cls.build_fhir_qualification(fhir_practitioner)
        return fhir_practitioner

    @classmethod
    def to_imis_obj(cls, fhir_practitioner, audit_user_id):
        errors = []
        fhir_practitioner = Practitioner(**fhir_practitioner)
        imis_officer = EnrolmentOfficerPractitionerConverter.create_default_claim_admin(audit_user_id)
        cls.build_imis_identifiers(imis_officer, fhir_practitioner, errors)
        cls.build_imis_names(imis_officer, fhir_practitioner)
        cls.build_imis_birth_date(imis_officer, fhir_practitioner)
        cls.build_imis_contacts(imis_officer, fhir_practitioner)
        cls.check_errors(errors)
        return imis_officer

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

    @classmethod
    def get_reference_obj_uuid(cls, imis_officer: Officer):
        return imis_officer.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_officer: Officer):
        return imis_officer.id

    @classmethod
    def get_reference_obj_code(cls, imis_officer: Officer):
        return imis_officer.code

    @classmethod
    def get_fhir_resource_type(cls):
        return Practitioner

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        return DbManagerUtils.get_object_or_none(
            Officer,
            **cls.get_database_query_id_parameteres_from_reference(reference))


    @classmethod
    def create_default_claim_admin(cls, audit_user_id):
        imis_officer = Officer()
        imis_officer.validity_from = TimeUtils.now()
        imis_officer.audit_user_id = audit_user_id
        return imis_officer

    @classmethod
    def build_fhir_identifiers(cls, fhir_practitioner, imis_officer):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_officer)
        fhir_practitioner.identifier = identifiers

    @classmethod
    def build_fhir_code_identifier(cls, identifiers, imis_officer):
        if imis_officer.code:
            identifier = cls.build_fhir_identifier(imis_officer.code,
                                                   R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                   R4IdentifierConfig.get_fhir_generic_type_code())
            identifiers.append(identifier)

    @classmethod
    def build_imis_identifiers(cls, imis_officer, fhir_practitioner, errors):
        value = cls.get_fhir_identifier_by_code(fhir_practitioner.identifier,
                                                R4IdentifierConfig.get_fhir_generic_type_code())
        if value:
            imis_officer.code = value
        cls.valid_condition(imis_officer.code is None, _('Missing the claim admin code'), errors)

    @classmethod
    def build_human_names(cls, fhir_practitioner, imis_officer):
        name = cls.build_fhir_names_for_person(imis_officer)
        fhir_practitioner.name = [name]

    @classmethod
    def build_imis_names(cls, imis_officer, fhir_practitioner):
        names = fhir_practitioner.name
        imis_officer.last_name, imis_officer.other_names = cls.build_imis_last_and_other_name(names)

    @classmethod
    def build_fhir_birth_date(cls, fhir_practitioner, imis_officer):
        if imis_officer.dob is not None:
            from core import datetime
            # check if datetime object
            if isinstance(imis_officer.dob, datetime.datetime):
                fhir_practitioner.birthDate = imis_officer.dob.date().isoformat()
            else:
                fhir_practitioner.birthDate = imis_officer.dob.isoformat()

    @classmethod
    def build_imis_birth_date(cls, imis_officer, fhir_practitioner):
        birth_date = fhir_practitioner.birthDate
        if birth_date:
            imis_officer.dob = TimeUtils.str_to_date(birth_date)

    @classmethod
    def build_fhir_telecom(cls, fhir_practitioner, imis_officer):
        fhir_practitioner.telecom = cls.build_fhir_telecom_for_person(phone=imis_officer.phone,
                                                                      email=imis_officer.email)

    @classmethod
    def build_imis_contacts(cls, imis_officer, fhir_practitioner):
        imis_officer.phone, imis_officer.email = cls.build_imis_phone_num_and_email(fhir_practitioner.telecom)

    @classmethod
    def build_fhir_qualification(cls, fhir_practitioner):
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/practitioner-qualification-type"
        qualification = PractitionerQualification.construct()
        qualification.code = cls.build_codeable_concept(
            system=system,
            code="EO",
            display=_("Enrolment Officer")
        )
        fhir_practitioner.qualification = [qualification]
