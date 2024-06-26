from urllib.parse import urljoin

from django.utils.translation import gettext as _
from fhir.resources.R4B.address import Address
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.humanname import HumanName

from api_fhir_r4.mapping.organizationMapping import PolicyHolderOrganisationLegalFormMapping, \
    PolicyHolderOrganisationActivityMapping
from api_fhir_r4.models.imisModelEnums import ImisLocationType, ContactPointSystem, AddressType
from location.models import Location
from policyholder.models import PolicyHolder
from api_fhir_r4.configurations import R4IdentifierConfig, R4OrganisationConfig, GeneralConfiguration
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from fhir.resources.R4B.organization import Organization
from api_fhir_r4.utils import DbManagerUtils


class PolicyHolderOrganisationConverter(BaseFHIRConverter, ReferenceConverterMixin):
    @classmethod
    def to_fhir_obj(cls, imis_organisation, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_organisation = Organization()
        cls.build_fhir_pk(fhir_organisation, imis_organisation, reference_type)
        cls.build_fhir_extensions(fhir_organisation, imis_organisation)
        cls.build_fhir_identifiers(fhir_organisation, imis_organisation, reference_type)
        cls.build_fhir_type(fhir_organisation)
        cls.build_fhir_name(fhir_organisation, imis_organisation)
        cls.build_fhir_telecom(fhir_organisation, imis_organisation)
        cls.build_fhir_ph_address(fhir_organisation, imis_organisation, reference_type)
        cls.build_fhir_contact(fhir_organisation, imis_organisation)
        return fhir_organisation

    @classmethod
    def to_imis_obj(cls, fhir_organisation, audit_user_id):
        raise NotImplementedError(
            _('PH Organization to_imis_obj() not implemented.')
        )

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        return DbManagerUtils.get_object_or_none(
            PolicyHolder,
            **cls.get_database_query_id_parameteres_from_reference(reference))

    @classmethod
    def get_reference_obj_id(cls, obj):
        return obj.uuid

    @classmethod
    def get_reference_obj_uuid(cls, obj):
        return obj.uuid

    @classmethod
    def get_reference_obj_code(cls, obj):
        return obj.code

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

    @classmethod
    def get_fhir_resource_type(cls):
        return Organization

    @classmethod
    def build_fhir_identifiers(cls, fhir_organisation, imis_organisation, reference_type):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_organisation, reference_type)
        fhir_organisation.identifier = identifiers

    @classmethod
    def build_fhir_extensions(cls, fhir_organisation, imis_organisation):
        if imis_organisation.legal_form:
            cls.build_fhir_legal_form_extension(fhir_organisation, imis_organisation)
        if imis_organisation.activity_code:
            cls.build_fhir_activity_extension(fhir_organisation, imis_organisation)

    @classmethod
    def build_fhir_legal_form_extension(cls, fhir_organisation, imis_organisation):
        codeable_concept = cls.build_codeable_concept_from_coding(cls.build_fhir_mapped_coding(
            PolicyHolderOrganisationLegalFormMapping.fhir_ph_code_system(imis_organisation.legal_form)
        ))
        base = GeneralConfiguration.get_system_base_url()
        url = urljoin(base, R4OrganisationConfig.get_fhir_ph_organisation_legal_form_extension_system())
        extension = cls.build_fhir_codeable_concept_extension(codeable_concept, url)
        if isinstance(fhir_organisation.extension, list):
            fhir_organisation.extension.append(extension)
        else:
            fhir_organisation.extension = [extension]

    @classmethod
    def build_fhir_activity_extension(cls, fhir_organisation, imis_organisation):
        codeable_concept = cls.build_codeable_concept_from_coding(cls.build_fhir_mapped_coding(
            PolicyHolderOrganisationActivityMapping.fhir_ph_code_system(imis_organisation.activity_code)
        ))
        base = GeneralConfiguration.get_system_base_url()
        url = urljoin(base, R4OrganisationConfig.get_fhir_ph_organisation_activity_extension_system())
        extension = cls.build_fhir_codeable_concept_extension(codeable_concept, url)
        if isinstance(fhir_organisation.extension, list):
            fhir_organisation.extension.append(extension)
        else:
            fhir_organisation.extension = [extension]

    @classmethod
    def build_fhir_type(cls, fhir_organisation):
        fhir_organisation.type = [cls.build_codeable_concept(
            R4OrganisationConfig.get_fhir_ph_organisation_type(),
            system=R4OrganisationConfig.get_fhir_ph_organisation_type_system()
        )]

    @classmethod
    def build_fhir_name(cls, fhir_organisation, imis_organisation):
        fhir_organisation.name = imis_organisation.trade_name

    @classmethod
    def build_fhir_telecom(cls, fhir_organisation, imis_organisation):
        fhir_organisation.telecom = []
        if imis_organisation.email:
            fhir_organisation.telecom.append(cls.build_fhir_contact_point(
                system=ContactPointSystem.EMAIL,
                value=imis_organisation.email))
        if imis_organisation.fax:
            fhir_organisation.telecom.append(cls.build_fhir_contact_point(
                system=ContactPointSystem.FAX,
                value=imis_organisation.fax))
        if imis_organisation.phone:
            fhir_organisation.telecom.append(cls.build_fhir_contact_point(
                system=ContactPointSystem.PHONE,
                value=imis_organisation.phone))

    @classmethod
    def build_fhir_ph_address(cls, fhir_organisation, imis_organisation, reference_type):
        address = Address.construct()
        address.type = AddressType.PHYSICAL.value
        if imis_organisation.address and "address" in imis_organisation.address:
            address.line = [imis_organisation.address["address"]]
        fhir_organisation.address = [address]
        if imis_organisation.locations:
            cls.build_fhir_address_field(fhir_organisation, imis_organisation.locations)
            cls.build_fhir_location_extension(fhir_organisation, imis_organisation, reference_type)

    @classmethod
    def build_fhir_address_field(cls, fhir_organisation, location: Location):
        current_location = location
        while current_location:
            if current_location.type == ImisLocationType.REGION.value:
                fhir_organisation.address[0].state = current_location.name
            elif current_location.type == ImisLocationType.DISTRICT.value:
                fhir_organisation.address[0].district = current_location.name
            elif current_location.type == ImisLocationType.WARD.value:
                cls.build_fhir_municipality_extension(fhir_organisation, current_location)
            elif current_location.type == ImisLocationType.VILLAGE.value:
                fhir_organisation.address[0].city = current_location.name
            current_location = current_location.parent

    @classmethod
    def build_fhir_municipality_extension(cls, fhir_organisation, municipality: Location):
        extension = Extension.construct()
        base = GeneralConfiguration.get_system_base_url()
        extension.url = urljoin(base, R4OrganisationConfig.get_fhir_address_municipality_extension_system())
        extension.valueString = municipality.name
        if isinstance(fhir_organisation.address[0].extension, list):
            fhir_organisation.address[0].extension.append(extension)
        else:
            fhir_organisation.address[0].extension = [extension]

    @classmethod
    def build_fhir_location_extension(cls, fhir_organisation, imis_organisation, reference_type):
        base = GeneralConfiguration.get_system_base_url()
        url = urljoin(base, R4OrganisationConfig.get_fhir_location_reference_extension_system())
        extension = cls.build_fhir_reference_extension(cls.build_fhir_resource_reference
                                                       (imis_organisation.locations,
                                                        type='Location',
                                                        display=imis_organisation.locations.name,
                                                        reference_type=reference_type),
                                                       url)
        if isinstance(fhir_organisation.address[0].extension, list):
            fhir_organisation.address[0].extension.append(extension)
        else:
            fhir_organisation.address[0].extension = [extension]

    @classmethod
    def build_fhir_contact(cls, fhir_organisation, imis_organisation):
        fhir_organisation.contact = []
        if imis_organisation.contact_name:
            name = HumanName.construct()
            name.text = "%s %s" % (imis_organisation.contact_name['name'], imis_organisation.contact_name['surname'])
            fhir_organisation.contact.append({'name': name})
