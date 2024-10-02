from abc import ABC
from typing import Union

from django.db.models import Model
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.money import Money
from fhir.resources.R4B.quantity import Quantity

import core
from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.exceptions import FHIRRequestProcessException
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.contactpoint import ContactPoint
from fhir.resources.R4B.address import Address
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.reference import Reference
from fhir.resources.R4B.identifier import Identifier
from api_fhir_r4.configurations import GeneralConfiguration
from uuid import UUID

class BaseFHIRConverter(ABC):

    user = None
    def __init__(self, user=None):
        if user:
            self.user = user
        else:
            raise Exception("Converter init need a valid user")
            
    
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
    def build_codeable_concept(cls, code, system=None, text=None, display=None):
        codeable_concept = CodeableConcept.construct()
        if code or system:
            coding = Coding.construct()

            if GeneralConfiguration.show_system():
                coding.system = system

            coding.code = str(code)

            if display:
                coding.display = str(display)
            codeable_concept.coding = [coding]

        if text:
            codeable_concept.text = text
        return codeable_concept

    @classmethod
    def build_codeable_concept_from_coding(cls, coding, text=None):
        codeable_concept = CodeableConcept.construct()

        if coding:
            codeable_concept.coding = [coding]

        if text:
            codeable_concept.text = str(text)

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
    def build_all_identifiers(cls, identifiers, imis_object, reference_type=None):
        cls.build_fhir_uuid_identifier(identifiers, imis_object)
        cls.build_fhir_code_identifier(identifiers, imis_object)
        if reference_type == ReferenceConverterMixin.DB_ID_REFERENCE_TYPE:
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
    def get_fhir_extension_by_url(cls, extensions, url):
        return next(iter([extension for extension in extensions if extension.url == url]), None)

    @classmethod
    def get_code_from_extension_codeable_concept(cls, extension):
        return extension.valueCodeableConcept.coding[0].code

    @classmethod
    def get_use_context_by_code(cls, use_context, code):
        return next(iter([entry for entry in use_context if entry.code.code == code]), None)

    @classmethod
    def build_fhir_contact_point(cls, value, system=None, use=None):
        contact_point = ContactPoint.construct()
        if system and GeneralConfiguration.show_system():
            contact_point.system = system.value

        if use:
            contact_point.use = use.value

        contact_point.value = value
        return contact_point

    @classmethod
    def get_contract_points_by_system_code(cls, telecom, system=None):
        return [contact.value for contact in telecom if contact.system == system]

    @classmethod
    def build_fhir_address(cls, value, use, type):
        current_address = Address.construct()
        if value:
            current_address.text = value
        current_address.use = use
        current_address.type = type
        return current_address

    @classmethod
    def build_fhir_reference(cls, identifier, display, ref_type, reference):
        fhir_reference = Reference.construct()
        fhir_reference.identifier = identifier
        fhir_reference.display = display
        fhir_reference.type = ref_type
        fhir_reference.reference = reference
        return fhir_reference

    @classmethod
    def build_fhir_mapped_coding(cls, mapping) -> Coding:
        coding = Coding.construct()

        if GeneralConfiguration.show_system():
            coding.system = mapping["system"]
        coding.code = mapping["code"]
        coding.display = mapping["display"]

        return coding

    @classmethod
    def build_fhir_reference_extension(cls, reference: Reference, url):
        extension = Extension.construct()
        extension.url = url
        extension.valueReference = reference
        return extension

    @classmethod
    def build_fhir_codeable_concept_extension(cls, codeable_concept: CodeableConcept, url):
        extension = Extension.construct()
        extension.url = url
        extension.valueCodeableConcept = codeable_concept
        return extension

    @classmethod
    def build_fhir_money(cls, value, currency=None):
        money = Money.construct()
        money.value = value
        if currency:
            money.currency = currency
        elif hasattr(core, 'currency'):
            money.currency = core.currency
        return money

    @classmethod
    def build_fhir_quantity(cls, value):
        quantity = Quantity.construct()
        quantity.value = value
        return quantity

    @classmethod
    def get_id_from_reference(cls, reference):
        splited_reference_string = reference.reference.split('/')
        id_from_reference = splited_reference_string.pop()
        return id_from_reference

    @classmethod
    def build_imis_identifier(cls, imis_obj, fhir_obj, errors):
        history_model = issubclass(imis_obj.__class__, core.models.HistoryModel)
        code = cls.get_fhir_identifier_by_code(
            fhir_obj.identifier,
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        uuid_str = cls.get_fhir_identifier_by_code(
            fhir_obj.identifier,
            R4IdentifierConfig.get_fhir_uuid_type_code()
        )
        id_str = None
        if not history_model:
            id_str = cls.get_fhir_identifier_by_code(
                fhir_obj.identifier,
                R4IdentifierConfig.get_fhir_acsn_type_code()
            )
            if id_str:
                imis_obj.id = id_str
        if uuid_str:
            if history_model:
                imis_obj.id = UUID(uuid_str)
            else:
                imis_obj.uuid = UUID(uuid_str)
            # if we have the id th uuid in not used
        if code:
            imis_obj.code = code
        
from api_fhir_r4.converters.personConverterMixin import PersonConverterMixin
from api_fhir_r4.converters.referenceConverterMixin import ReferenceConverterMixin
from api_fhir_r4.converters.medicationConverter import MedicationConverter
from api_fhir_r4.converters.activityDefinitionConverter import ActivityDefinitionConverter
from api_fhir_r4.converters.contractConverter import ContractConverter
from api_fhir_r4.converters.patientConverter import PatientConverter
from api_fhir_r4.converters.groupConverter import GroupConverter
from api_fhir_r4.converters.policyHolderOrganisationConverter import PolicyHolderOrganisationConverter
from api_fhir_r4.converters.locationConverter import LocationConverter
from api_fhir_r4.converters.locationSiteConverter import LocationSiteConverter
from api_fhir_r4.converters.operationOutcomeConverter import OperationOutcomeConverter
from api_fhir_r4.converters.claimAdminPractitionerConverter import ClaimAdminPractitionerConverter
from api_fhir_r4.converters.claimAdminPractitionerRoleConverter import ClaimAdminPractitionerRoleConverter
from api_fhir_r4.converters.coverageEligibilityRequestConverter import CoverageEligibilityRequestConverter
# from api_fhir_r4.converters.policyCoverageEligibilityRequestConverter import PolicyCoverageEligibilityRequestConverter
from api_fhir_r4.converters.communicationRequestConverter import CommunicationRequestConverter
from api_fhir_r4.converters.claimResponseConverter import ClaimResponseConverter
from api_fhir_r4.converters.claimConverter import ClaimConverter
from api_fhir_r4.converters.insurancePlanConverter import InsurancePlanConverter
from api_fhir_r4.converters.codeSystemConverter import CodeSystemConverter
from api_fhir_r4.converters.healthFacilityOrganisationConverter import HealthFacilityOrganisationConverter
from api_fhir_r4.converters.insuranceOrganisationConverter import InsuranceOrganisationConverter
from api_fhir_r4.converters.enrolmentOfficerPractitionerConverter import EnrolmentOfficerPractitionerConverter
from api_fhir_r4.converters.enrolmentOfficerPractitionerRoleConverter import EnrolmentOfficerPractitionerRoleConverter
from api_fhir_r4.converters.communicationConverter import CommunicationConverter
from api_fhir_r4.converters.coverageConverter import CoverageConverter
from api_fhir_r4.converters.invoiceConverter import InvoiceConverter, BillInvoiceConverter
