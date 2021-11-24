from medical.models import Diagnosis
from api_fhir_r4.converters import R4IdentifierConfig, BaseFHIRConverter, ReferenceConverterMixin
from fhir.resources.reference import Reference
from fhir.resources.condition import Condition as FHIRCondition
from django.utils.translation import gettext
from api_fhir_r4.utils import DbManagerUtils, TimeUtils


class ConditionConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_condition, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_condition = FHIRCondition.construct()
        cls.build_fhir_pk(fhir_condition, imis_condition, reference_type)
        cls.build_fhir_identifiers(fhir_condition, imis_condition)
        cls.build_fhir_codes(fhir_condition, imis_condition)
        cls.build_fhir_recorded_date(fhir_condition, imis_condition)
        cls.build_fhir_subject(fhir_condition)
        return fhir_condition

    @classmethod
    def to_imis_obj(cls, fhir_condition, audit_user_id):
        errors = []
        fhir_condition = FHIRCondition(**fhir_condition)
        imis_condition = Diagnosis()
        cls.build_imis_identifier(imis_condition, fhir_condition, errors)
        cls.build_imis_validity_from(imis_condition, fhir_condition, errors)
        cls.build_imis_icd_code(imis_condition, fhir_condition, errors)
        cls.build_imis_icd_name(imis_condition, fhir_condition, errors)
        imis_condition.audit_user_id = audit_user_id
        cls.check_errors(errors)
        return imis_condition

    @classmethod
    def build_fhir_pk(cls, fhir_obj, resource, reference_type):
        if not reference_type:
            cls._build_simple_pk(fhir_obj, resource)
        if reference_type == ReferenceConverterMixin.UUID_REFERENCE_TYPE:
            # id as string because of db, has to be changed to uuid
            fhir_obj.id = str(resource.id)
        elif reference_type == ReferenceConverterMixin.DB_ID_REFERENCE_TYPE:
            fhir_obj.id = resource.id
        elif reference_type == ReferenceConverterMixin.CODE_REFERENCE_TYPE:
            fhir_obj.id = resource.code

    @classmethod
    def build_reference_identifier(cls, obj, reference_type):
        # Regardless of reference type diagnosis identifier is string format is used
        identifiers = []
        return cls.build_fhir_id_identifier(identifiers, obj)

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_diagnosis_code_type()

    @classmethod
    def get_reference_obj_uuid(cls, imis_condition: Diagnosis):
        # Diagnosis don't have uuid value
        return str(imis_condition.id)

    @classmethod
    def get_reference_obj_id(cls, imis_condition: Diagnosis):
        return imis_condition.id

    @classmethod
    def get_reference_obj_code(cls, imis_condition: Diagnosis):
        return imis_condition.code

    @classmethod
    def get_fhir_resource_type(cls):
        return FHIRCondition

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_condition_code = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Diagnosis, code=imis_condition_code)

    @classmethod
    def build_fhir_identifiers(cls, fhir_condition, imis_condition):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_condition)
        fhir_condition.identifier = identifiers

    @classmethod
    def build_imis_identifier(cls, imis_condition, fhir_condition, errors):
        value = cls.get_fhir_identifier_by_code(fhir_condition.identifier, R4IdentifierConfig.get_fhir_claim_code_type())
        if value:
            imis_condition.code = value
        cls.valid_condition(imis_condition.code is None, gettext('Missing the ICD code'), errors)

    @classmethod
    def build_fhir_recorded_date(cls, fhir_condition, imis_condition):
        fhir_condition.recordedDate = imis_condition.validity_from.isoformat()

    @classmethod
    def build_imis_validity_from(cls, imis_condition, fhir_condition, errors):
        validity_from = fhir_condition.recordedDate
        if not cls.valid_condition(validity_from is None,
                                   gettext('Missing condition `recorded_date` attribute'), errors):
            imis_condition.validity_from = TimeUtils.str_to_date(validity_from)

    @classmethod
    def build_fhir_codes(cls, fhir_condition, imis_condition):
        fhir_condition.code = cls.build_codeable_concept(imis_condition.code, text=imis_condition.name)

    @classmethod
    def build_imis_icd_code(cls, imis_condition, fhir_condition, errors):
        icd_code = fhir_condition.code.coding
        if not cls.valid_condition(icd_code is None,
                                   gettext('Missing condition `icd_code` attribute'), errors):

            # get the code of condition/diagnosis
            if type(icd_code) is not list:
                imis_condition.code = icd_code.code
            else:
                icd_code_element = icd_code[0]
                imis_condition.code = icd_code_element.code

    @classmethod
    def build_imis_icd_name(cls, imis_condition, fhir_condition, errors):
        icd_name = fhir_condition.code.text
        if not cls.valid_condition(icd_name is None,
                                   gettext('Missing condition `icd_name` attribute'), errors):
            imis_condition.name = icd_name

    @classmethod
    def build_fhir_subject(cls, fhir_condition):
        reference = Reference.construct()
        reference.type = "Patient"
        fhir_condition.subject = reference
