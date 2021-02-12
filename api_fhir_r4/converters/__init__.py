from abc import ABC

from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.exceptions import FHIRRequestProcessException
from api_fhir_r4.models import CodeableConcept, ContactPoint, Address, Coding, Identifier, IdentifierUse, Reference
from api_fhir_r4.configurations import GeneralConfiguration


class BaseFHIRConverter(ABC):

    @classmethod
    def to_fhir_obj(cls, obj):
        raise NotImplementedError('`toFhirObj()` must be implemented.')  # pragma: no cover

    @classmethod
    def to_imis_obj(cls, data, audit_user_id):
        raise NotImplementedError('`toImisObj()` must be implemented.')  # pragma: no cover

    @classmethod
    def build_fhir_pk(cls, fhir_obj, resource_id):
        fhir_obj.id = resource_id

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
        codeable_concept = CodeableConcept()
        if code or system:
            coding = Coding()
            if GeneralConfiguration.show_system():
                coding.system = system
            if not isinstance(code, str):
                code = str(code)
            coding.code = code
            codeable_concept.coding = [coding]
        codeable_concept.text = text
        return codeable_concept

    @classmethod
    def get_first_coding_from_codeable_concept(cls, codeable_concept):
        result = Coding()
        if codeable_concept:
            coding = codeable_concept.coding
            if coding and isinstance(coding, list) and len(coding) > 0:
                result = codeable_concept.coding[0]
        return result

    @classmethod
    def build_fhir_uuid_identifier(cls, identifiers, imis_object):
        if hasattr(imis_object,'uuid') and imis_object.uuid is not None:
            identifier = cls.build_fhir_identifier(imis_object.uuid,
                                                   R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                   R4IdentifierConfig.get_fhir_uuid_type_code())
            identifiers.append(identifier)
        elif hasattr(imis_object,'id') and imis_object.id is not None:
            identifier = cls.build_fhir_identifier(imis_object.id,
                                                   R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                   R4IdentifierConfig.get_fhir_uuid_type_code())
            identifiers.append(identifier)
        else:
            raise FHIRRequestProcessException(['Cannot construct an identifier, the object has no uuid nor id: {}'])


    @classmethod
    def build_fhir_identifier(cls, value, type_system, type_code):
        identifier = Identifier()
        identifier.use = IdentifierUse.USUAL.value
        type = cls.build_codeable_concept(type_code, type_system)
        identifier.type = type
        identifier.value = value
        return identifier

    @classmethod
    def get_fhir_identifier_by_code(cls, identifiers, lookup_code):
        value = None
        for identifier in identifiers or []:
            first_coding = cls.get_first_coding_from_codeable_concept(identifier.type)
            if first_coding.system == R4IdentifierConfig.get_fhir_identifier_type_system() \
                and first_coding.code == lookup_code:
                value = identifier.value
                break
        return value

    @classmethod
    def build_fhir_contact_point(cls, value, contact_point_system, contact_point_use):
        contact_point = ContactPoint()
        if GeneralConfiguration.show_system():
            contact_point.system = contact_point_system
        contact_point.use = contact_point_use
        contact_point.value = value
        return contact_point

    @classmethod
    def build_fhir_address(cls, value, use, type):
        current_address = Address()
        current_address.text = value
        current_address.use = use
        current_address.type = type
        return current_address
    
    @classmethod
    def build_fhir_address(cls, value, use, type):
        current_address = Address()
        current_address.text = value
        current_address.use = use
        current_address.type = type
        return current_address
    @classmethod
    def build_fhir_reference(cls, identifier, display, type, reference):
        reference = Reference()
        reference.identifier = identifier
        reference.display = display
        reference.type = type
        reference.reference = reference
        return reference
from api_fhir_r4.converters.groupConverterMixin import GroupConverterMixin
from api_fhir_r4.converters.organisationConverterMixin import OrganisationConverterMixin
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
from api_fhir_r4.converters.medicationConverter import MedicationConverter
from api_fhir_r4.converters.conditionConverter import ConditionConverter
from api_fhir_r4.converters.activityDefinitionConverter import ActivityDefinitionConverter
from api_fhir_r4.converters.healthcareServiceConverter import HealthcareServiceConverter
