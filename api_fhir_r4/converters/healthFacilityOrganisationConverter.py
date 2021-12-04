import logging

from location.models import HealthFacility
from claim.models import ClaimAdmin
from fhir.resources.address import Address

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin, LocationConverter, PersonConverterMixin
from fhir.resources.organization import Organization
from fhir.resources.organization import OrganizationContact
from fhir.resources.extension import Extension
from api_fhir_r4.mapping.hfOrganizationMapping import HealthFacilityOrganizationTypeMapping
from api_fhir_r4.utils import DbManagerUtils

logger = logging.getLogger(__name__)


class HealthFacilityOrganisationConverter(BaseFHIRConverter, PersonConverterMixin, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_organisation: HealthFacility, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_organisation = Organization()
        cls.build_fhir_pk(fhir_organisation, imis_organisation, reference_type)
        cls.build_fhir_extensions(fhir_organisation, imis_organisation)
        cls.build_fhir_identifiers(fhir_organisation, imis_organisation)
        cls.build_fhir_type(fhir_organisation, imis_organisation)
        cls.build_fhir_name(fhir_organisation, imis_organisation)
        cls.build_fhir_telecom(fhir_organisation, imis_organisation)
        cls.build_hf_address(fhir_organisation, imis_organisation, reference_type)
        cls.build_contacts(fhir_organisation, imis_organisation)
        return fhir_organisation

    @classmethod
    def to_imis_obj(cls, fhir_organisation, audit_user_id):
        raise NotImplementedError(
            'HF Organisation to_imis_obj() not implemented. '
            'Instance should be created/updated using Practitioner resource.'
        )

    @classmethod
    def get_fhir_resource_type(cls):
        return Organization

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        healthfacility_uuid = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(HealthFacility, uuid=healthfacility_uuid)

    @classmethod
    def build_fhir_extensions(cls, fhir_organisation: Organization, imis_organisation: HealthFacility):
        extensions = [
            cls.__legal_form_extension(),
            cls.__level_extension(imis_organisation),
            cls.__type_extension(imis_organisation)
        ]
        fhir_organisation.extension = [ext for ext in extensions if ext]

    @classmethod
    def build_fhir_identifiers(cls, fhir_organisation, imis_organisation):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_organisation)
        fhir_organisation.identifier = identifiers

    @classmethod
    def build_fhir_type(cls, fhir_organisation, imis_organisation):
        organisation_type = cls.build_codeable_concept(code=HealthFacilityOrganizationTypeMapping.ORGANIZATION_TYPE)
        fhir_organisation.type = [organisation_type]

    @classmethod
    def build_fhir_name(cls, fhir_organisation: Organization, imis_organisation: HealthFacility):
        name = imis_organisation.name
        fhir_organisation.name = name

    @classmethod
    def build_fhir_telecom(cls, fhir_organisation: Organization, imis_organisation: HealthFacility):
        telecom = []
        imis_organisation.email = 'test_email'
        imis_organisation.phone = 'test_phone'
        imis_organisation.fax = 'test_fax'

        if imis_organisation.email:
            telecom.append(cls._build_email_contact_point(imis_organisation))

        if imis_organisation.phone:
            telecom.append(cls._build_phone_contact_point(imis_organisation))

        if imis_organisation.fax:
            telecom.append(cls._build_fax_contact_point(imis_organisation))

        fhir_organisation.telecom = telecom

    @classmethod
    def _build_email_contact_point(cls, imis_organisation):
        return cls.build_fhir_contact_point(
            value=imis_organisation.email,
            contact_point_system=HealthFacilityOrganizationTypeMapping.EMAIL_CONTACT_POINT_SYSTEM
        )

    @classmethod
    def _build_phone_contact_point(cls, imis_organisation):
        return cls.build_fhir_contact_point(
            value=imis_organisation.phone,
            contact_point_system=HealthFacilityOrganizationTypeMapping.PHONE_CONTACT_POINT_SYSTEM
        )

    @classmethod
    def _build_fax_contact_point(cls, imis_organisation):
        return cls.build_fhir_contact_point(
            value=imis_organisation.fax,
            contact_point_system=HealthFacilityOrganizationTypeMapping.FAX_CONTACT_POINT_SYSTEM
        )

    @classmethod
    def build_hf_address(cls, fhir_organisation: Organization, imis_organisation: HealthFacility, reference_type):
        address = Address.construct()
        if imis_organisation.address:
            address.line = [imis_organisation.address]

        # Hospitals are expected to be on district level
        address.district = imis_organisation.location.name
        address.state = imis_organisation.location.parent.name
        address.type = 'physical'
        address.extension = [cls._build_address_ext(imis_organisation, reference_type)]

        fhir_organisation.address = [address]

    @classmethod
    def _build_address_ext(cls, imis_organisation, reference_type):
        address_ref = LocationConverter.build_fhir_resource_reference(imis_organisation, 'Organisation', reference_type=reference_type)
        address_ext = Extension.construct()
        address_ext.url = HealthFacilityOrganizationTypeMapping.ADDRESS_LOCATION_REFERENCE_URL
        address_ext.valueReference = address_ref
        return address_ext

    @classmethod
    def build_contacts(cls, fhir_organisation, imis_organisation):
        contracts = []
        relevant_claim_admins = ClaimAdmin.objects.filter(health_facility=imis_organisation)

        for admin in relevant_claim_admins:
            contracts.append(
                cls._build_claim_admin_contract(admin)
            )

        fhir_organisation.contact = contracts

    @classmethod
    def _build_claim_admin_contract(cls, admin):
        contract = OrganizationContact.construct()
        contract.purpose = cls.build_codeable_concept(**HealthFacilityOrganizationTypeMapping.CONTRACT_PURPOSE)
        name = cls.build_fhir_names_for_person(admin)
        contract.name = name
        return contract

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_location_code_type()

    @classmethod
    def get_reference_obj_uuid(cls, imis_organisation):
        return imis_organisation.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_organisation):
        return imis_organisation.id

    @classmethod
    def get_reference_obj_code(cls, imis_organisation):
        return imis_organisation.code

    @classmethod
    def __legal_form_extension(cls):
        extension = Extension.construct()
        extension.url = f'{GeneralConfiguration.get_system_base_url()}StructureDefinition/organization-legal-form'
        extension.valueCodeableConcept = cls.build_codeable_concept(
            code=HealthFacilityOrganizationTypeMapping.LEGAL_FORM_CODE,
            system=HealthFacilityOrganizationTypeMapping.LEGAL_FORM_SYSTEM,
            display=HealthFacilityOrganizationTypeMapping.LEGAL_FORM_DISPLAY
        )
        return extension

    @classmethod
    def __level_extension(cls, imis_organisation):
        if not imis_organisation.level:
            return

        level = imis_organisation.level

        level_display = HealthFacilityOrganizationTypeMapping.LEVEL_DISPLAY_MAPPING.get(level, None)
        if not level_display:
            logger.warning(f'Failed to build level display for HF Level {level}.')

        extension = Extension.construct()
        extension.url = f'{GeneralConfiguration.get_system_base_url()}/StructureDefinition/organization-hf-level'
        extension.valueCodeableConcept = cls.build_codeable_concept(
            code=level,
            system=HealthFacilityOrganizationTypeMapping.LEVEL_SYSTEM,
            display=level_display
        )

        return extension

    @classmethod
    def __type_extension(cls, imis_organisation: HealthFacility):
        care_type = imis_organisation.care_type
        care_type_display = HealthFacilityOrganizationTypeMapping.TYPE_DISPLAY_MAPPING.get(care_type, None)

        extension = Extension.construct()
        extension.url = f'{GeneralConfiguration.get_system_base_url()}StructureDefinition/organization-hf-care-type'
        extension.valueCodeableConcept = cls.build_codeable_concept(
            code=care_type,
            system=HealthFacilityOrganizationTypeMapping.TYPE_SYSTEM,
            display=care_type_display
        )
        return extension
