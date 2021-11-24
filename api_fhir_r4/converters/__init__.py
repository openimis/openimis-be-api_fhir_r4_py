from abc import ABC
from typing import Union

from django.db.models import Model

from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.exceptions import FHIRRequestProcessException
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.address import Address
from fhir.resources.coding import Coding
from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier
from api_fhir_r4.configurations import GeneralConfiguration


class BaseFHIRConverter(ABC):

    @classmethod
    def to_fhir_obj(cls, obj, reference_type):
        raise NotImplementedError('`toFhirObj()` must be implemented.')  # pragma: no cover

    @classmethod
    def to_imis_obj(cls, data, audit_user_id):
        raise NotImplementedError('`toImisObj()` must be implemented.')  # pragma: no cover

    @classmethod
    def get_fhir_code_identifier_type(cls):
        raise NotImplementedError('get_fhir_code_identifier_type() must be implemented')

    @classmethod
    def _build_simple_pk(cls, fhir_obj, resource_id):
        if type(resource_id) is not str:
            resource_id = str(resource_id)
        fhir_obj.id = resource_id

    @classmethod
    def build_fhir_pk(cls, fhir_obj, resource: Union[str, Model], reference_type: str = None):
        if not reference_type:
            cls._build_simple_pk(fhir_obj, resource)
        if reference_type == ReferenceConverterMixin.UUID_REFERENCE_TYPE:
            # OE0-18 - change into string type uuid
            fhir_obj.id = str(resource.uuid)
        elif reference_type == ReferenceConverterMixin.DB_ID_REFERENCE_TYPE:
            fhir_obj.id = str(resource.id)
        elif reference_type == ReferenceConverterMixin.CODE_REFERENCE_TYPE:
            fhir_obj.id = resource.code

    @classmethod
    def valid_condition(cls, condition, error_message, errors=None):
        if errors is None:
            errors = []
        if condition:
            errors.append(error_message)
        return condition

    @classmethod
    def check_errors(cls, errors=None):  # pragma: no cover
        if errors is None:
            errors = []
        if len(errors) > 0:
            raise FHIRRequestProcessException(errors)

    @classmethod
    def build_simple_codeable_concept(cls, text):
        return cls.build_codeable_concept(None, None, text)

    @classmethod
    def build_codeable_concept(cls, code, system=None, text=None):
        codeable_concept = CodeableConcept.construct()
        if code or system:
            coding = Coding.construct()
            if GeneralConfiguration.show_system():
                coding.system = system
            if not isinstance(code, str):
                code = str(code)
            coding.code = code
            codeable_concept.coding = [coding]

        if text:
            codeable_concept.text = text
        return codeable_concept

    @classmethod
    def get_first_coding_from_codeable_concept(cls, codeable_concept):
        result = Coding.construct()
        if codeable_concept:
            coding = codeable_concept.coding
            if coding and isinstance(coding, list) and len(coding) > 0:
                result = codeable_concept.coding[0]
        return result

    @classmethod
    def build_all_identifiers(cls, identifiers, imis_object):
        cls.build_fhir_uuid_identifier(identifiers, imis_object)
        cls.build_fhir_code_identifier(identifiers, imis_object)
        cls.build_fhir_id_identifier(identifiers, imis_object)
        return identifiers

    @classmethod
    def build_fhir_uuid_identifier(cls, identifiers, imis_object):
        if hasattr(imis_object, 'uuid'):
            identifiers.append(cls.__build_uuid_identifier(imis_object.uuid))

    @classmethod
    def build_fhir_id_identifier(cls, identifiers, imis_object):
        if hasattr(imis_object, 'id'):
            identifiers.append(cls.__build_id_identifier(str(imis_object.id)))

    @classmethod
    def build_fhir_code_identifier(cls, identifiers, imis_object):
        if hasattr(imis_object, 'code'):
            identifiers.append(cls.__build_code_identifier(imis_object.code))

    @classmethod
    def __build_uuid_identifier(cls, uuid):
        return cls.build_fhir_identifier(uuid,
                                         R4IdentifierConfig.get_fhir_identifier_type_system(),
                                         R4IdentifierConfig.get_fhir_uuid_type_code())

    @classmethod
    def __build_id_identifier(cls, db_id):
        return cls.build_fhir_identifier(db_id,
                                         R4IdentifierConfig.get_fhir_identifier_type_system(),
                                         R4IdentifierConfig.get_fhir_id_type_code())

    @classmethod
    def __build_code_identifier(cls, code):
        return cls.build_fhir_identifier(code,
                                         R4IdentifierConfig.get_fhir_identifier_type_system(),
                                         cls.get_fhir_code_identifier_type())

    @classmethod
    def build_fhir_identifier(cls, value, type_system, type_code):
        identifier = Identifier.construct()
        identifier.use = "usual"
        type = cls.build_codeable_concept(type_code, type_system)
        identifier.type = type
        # OE0-18 - change into string type always
        identifier.value = str(value)
        return identifier

    @classmethod
    def get_fhir_identifier_by_code(cls, identifiers, lookup_code):
        value = None
        for identifier in identifiers or []:
            first_coding = cls.get_first_coding_from_codeable_concept(identifier.type)
            if first_coding.code == lookup_code:
                value = identifier.value
                break
        return value

    @classmethod
    def build_fhir_contact_point(cls, value, contact_point_system, contact_point_use):
        contact_point = ContactPoint.construct()
        if GeneralConfiguration.show_system():
            contact_point.system = contact_point_system
        contact_point.use = contact_point_use
        contact_point.value = value
        return contact_point

    @classmethod
    def build_fhir_address(cls, value, use, type):
        current_address = Address.construct()
        current_address.text = value
        current_address.use = use
        current_address.type = type
        return current_address

    @classmethod
    def build_fhir_reference(cls, identifier, display, type, reference):
        reference = Reference.construct()
        reference.identifier = identifier
        reference.display = display
        reference.type = type
        reference.reference = reference
        return reference


from api_fhir_r4.converters.groupConverterMixin import GroupConverterMixin
from api_fhir_r4.converters.personConverterMixin import PersonConverterMixin
from api_fhir_r4.converters.referenceConverterMixin import ReferenceConverterMixin
from api_fhir_r4.converters.contractConverter import ContractConverter
from api_fhir_r4.converters.patientConverter import PatientConverter
from api_fhir_r4.converters.groupConverter import GroupConverter
from api_fhir_r4.converters.organisationConverter import OrganisationConverter
from api_fhir_r4.converters.locationConverter import LocationConverter
from api_fhir_r4.converters.locationSiteConverter import LocationSiteConverter
from api_fhir_r4.converters.operationOutcomeConverter import OperationOutcomeConverter
from api_fhir_r4.converters.practitionerConverter import PractitionerConverter
from api_fhir_r4.converters.practitionerRoleConverter import PractitionerRoleConverter
from api_fhir_r4.converters.coverageEligibilityRequestConverter import CoverageEligibilityRequestConverter
from api_fhir_r4.converters.policyCoverageEligibilityRequestConverter import PolicyCoverageEligibilityRequestConverter
from api_fhir_r4.converters.communicationRequestConverter import CommunicationRequestConverter
from api_fhir_r4.converters.claimResponseConverter import ClaimResponseConverter
from api_fhir_r4.converters.claimConverter import ClaimConverter
from api_fhir_r4.converters.medicationConverter import MedicationConverter
from api_fhir_r4.converters.conditionConverter import ConditionConverter
from api_fhir_r4.converters.activityDefinitionConverter import ActivityDefinitionConverter
from api_fhir_r4.converters.healthcareServiceConverter import HealthcareServiceConverter
from api_fhir_r4.converters.containedResourceConverter import ContainedResourceConverter
