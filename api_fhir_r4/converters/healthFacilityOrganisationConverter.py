import logging

from django.core.exceptions import MultipleObjectsReturned
from location.models import HealthFacility, Location, HealthFacilityLegalForm
from claim.models import ClaimAdmin
from fhir.resources.address import Address

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin, LocationConverter, PersonConverterMixin
from fhir.resources.organization import Organization
from fhir.resources.organization import OrganizationContact
from fhir.resources.extension import Extension
from api_fhir_r4.mapping.organizationMapping import HealthFacilityOrganizationTypeMapping
from api_fhir_r4.models.imisModelEnums import ImisLocationType
from api_fhir_r4.utils import DbManagerUtils
from django.utils.translation import gettext as _

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
        errors = []
        fhir_hf = Organization(**fhir_organisation)
        imis_hf = HealthFacility()
        imis_hf.audit_user_id = audit_user_id
        cls.build_imis_hf_identiftier(imis_hf, fhir_hf, errors)
        cls.build_imis_hf_name(imis_hf, fhir_hf, errors)
        cls.build_imis_hf_telecom(imis_hf, fhir_hf, errors)
        cls.build_imis_hf_address(imis_hf, fhir_hf, errors)
        cls.build_imis_hf_level(imis_hf, fhir_hf, errors)
        cls.build_imis_care_type(imis_hf, fhir_hf, errors)
        cls.build_imis_legal_form(imis_hf, fhir_hf, errors)
        cls.build_imis_parent_location_id(imis_hf, fhir_hf, errors)
        cls.check_errors(errors)
        return imis_hf

    @classmethod
    def get_fhir_resource_type(cls):
        return Organization

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        healthfacility_uuid = cls.get_resource_id_from_reference(reference).lower()
        return DbManagerUtils.get_object_or_none(HealthFacility, uuid=healthfacility_uuid)

    @classmethod
    def build_fhir_extensions(cls, fhir_organisation: Organization, imis_organisation: HealthFacility):
        extensions = [
            cls.__legal_form_extension(imis_organisation),
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
            system=HealthFacilityOrganizationTypeMapping.EMAIL_CONTACT_POINT_SYSTEM
        )

    @classmethod
    def _build_phone_contact_point(cls, imis_organisation):
        return cls.build_fhir_contact_point(
            value=imis_organisation.phone,
            system=HealthFacilityOrganizationTypeMapping.PHONE_CONTACT_POINT_SYSTEM
        )

    @classmethod
    def _build_fax_contact_point(cls, imis_organisation):
        return cls.build_fhir_contact_point(
            value=imis_organisation.fax,
            system=HealthFacilityOrganizationTypeMapping.FAX_CONTACT_POINT_SYSTEM
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
        address_ref = LocationConverter\
            .build_fhir_resource_reference(imis_organisation, 'Organization', reference_type=reference_type)
        address_ext = Extension.construct()
        address_ext.url = HealthFacilityOrganizationTypeMapping.ADDRESS_LOCATION_REFERENCE_URL
        address_ext.valueReference = address_ref
        return address_ext

    @classmethod
    def build_contacts(cls, fhir_organisation, imis_organisation):
        contracts = []
        relevant_claim_admins = ClaimAdmin.objects\
            .filter(health_facility=imis_organisation, validity_to__isnull=True).distinct()

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
    def __legal_form_extension(cls, imis_organisation: HealthFacility):
        if imis_organisation.legal_form:
            legal_form = imis_organisation.legal_form.code
            extension = Extension.construct()
            extension.url = f'{GeneralConfiguration.get_system_base_url()}StructureDefinition/organization-legal-form'
            extension.valueCodeableConcept = cls.build_codeable_concept(
                code=legal_form,
                system=HealthFacilityOrganizationTypeMapping.LEGAL_FORM_SYSTEM,
                display=HealthFacilityOrganizationTypeMapping.LEGAL_FORM_MAPPING.get(legal_form)
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
        if imis_organisation.care_type and imis_organisation.care_type != ' ':
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

    @classmethod
    def build_imis_hf_identiftier(cls, imis_hf, fhir_hf, errors):
        value = cls.get_fhir_identifier_by_code(
            fhir_hf.identifier,
            R4IdentifierConfig.get_fhir_generic_type_code()
        )

        if value:
            imis_hf.code = value
        cls.valid_condition(imis_hf.code is None, _('Missing HF Organization code'), errors)

    @classmethod
    def build_imis_hf_name(cls, imis_hf, fhir_hf, errors):
        imis_hf.name = fhir_hf.name
        cls.valid_condition(imis_hf.code is None, _('Missing HF Name'), errors)

    @classmethod
    def build_imis_hf_telecom(cls, imis_hf, fhir_hf, errors):
        cls._build_imis_hf_email(imis_hf, fhir_hf, errors)
        cls._build_imis_hf_fax(imis_hf, fhir_hf, errors)
        cls._build_imis_hf_phone(imis_hf, fhir_hf, errors)

    @classmethod
    def _build_imis_hf_email(cls, imis_hf, fhir_hf, errors):
        imis_hf.email = cls.__get_unique_telecom(
            fhir_hf,
            HealthFacilityOrganizationTypeMapping.EMAIL_CONTACT_POINT_SYSTEM,
            errors
        )

    @classmethod
    def _build_imis_hf_fax(cls, imis_hf, fhir_hf, errors):
        imis_hf.fax = cls.__get_unique_telecom(
            fhir_hf,
            HealthFacilityOrganizationTypeMapping.FAX_CONTACT_POINT_SYSTEM,
            errors
        )

    @classmethod
    def _build_imis_hf_phone(cls, imis_hf, fhir_hf, errors):
        imis_hf.phone = cls.__get_unique_telecom(
            fhir_hf,
            HealthFacilityOrganizationTypeMapping.PHONE_CONTACT_POINT_SYSTEM,
            errors
        )

    @classmethod
    def __get_unique_telecom(cls, fhir_hf, system, errors):
        if not fhir_hf.telecom:
            return None

        telecom = cls.get_contract_points_by_system_code(
            fhir_hf.telecom,
            HealthFacilityOrganizationTypeMapping.FAX_CONTACT_POINT_SYSTEM)

        cls.valid_condition(
            len(telecom) > 1,
            _(f'More than one contact point of system {system} assigned to health facility'),
            errors
        )
        return telecom[0] if telecom else None

    @classmethod
    def build_imis_hf_address(cls, imis_hf: HealthFacility, fhir_hf: Organization, errors):
        if fhir_hf.address:
            imis_hf.address = fhir_hf.address[0].line[0]

    @classmethod
    def build_imis_hf_level(cls, imis_hf, fhir_hf, errors):
        ext_url_suffix = 'organization-hf-level'
        imis_hf.level = cls.__get_extension_by_url_suffix(fhir_hf.extension, ext_url_suffix)

    @classmethod
    def build_imis_care_type(cls, imis_hf, fhir_hf, errors):
        ext_url_suffix = 'organization-hf-care-type'
        value = cls.__get_extension_by_url_suffix(fhir_hf.extension, ext_url_suffix)
        if value:
            imis_hf.care_type = value
        else:
            cls.valid_condition(True, _("Extension with HF care type not found"), errors)

    @classmethod
    def build_imis_legal_form(cls, imis_hf, fhir_hf, errors):
        ext_url_suffix = 'organization-legal-form'
        value = cls.__get_extension_by_url_suffix(fhir_hf.extension, ext_url_suffix)
        cls.valid_condition(
            value not in HealthFacilityOrganizationTypeMapping.LEGAL_FORM_MAPPING.keys(),
            _("Invalid HF legal form code, has to be one of %(codes)s") % {
                'codes': HealthFacilityOrganizationTypeMapping.LEGAL_FORM_MAPPING.keys()},
            errors)
        if value:
            legal_form = HealthFacilityLegalForm.objects.get(code=value)
            imis_hf.legal_form = legal_form
        else:
            cls.valid_condition(True, _("Extension with HF legal form not found"), errors)

    @classmethod
    def __get_extension_by_url_suffix(cls, extensions, ext_url_suffix):
        level_ext = next((x for x in extensions if x.url.endswith(ext_url_suffix)), None)
        if level_ext:
            return cls.get_first_coding_from_codeable_concept(
                level_ext.valueCodeableConcept).code
        else:
            return None

    @classmethod
    def build_imis_parent_location_id(cls, imis_hf, fhir_hf, errors):
        address = fhir_hf.address[0]
        matching_locations = Location.objects \
            .filter(
                validity_to__isnull=True,
                name=address.district,
                parent__name=address.state,
                type="D"  # HF is expected to be at district level
            ).distinct()\
            .all()

        if matching_locations.count() != 1:
            msg = cls.__get_invalid_location_msg(address, matching_locations)
            cls.valid_condition(matching_locations.count() == 1, msg, errors)
            return
        else:
            imis_hf.location = matching_locations.first()

    @classmethod
    def __get_invalid_location_msg(cls, address, matching_locations):
        count = matching_locations.count()
        if count == 0:
            return _(F"No matching location for district {address.district}, state {address.state}.")
        elif count > 1:
            return _(F"More than one matching location district {address.district}, state {address.state}:\n"
                     F"{matching_locations}.")
