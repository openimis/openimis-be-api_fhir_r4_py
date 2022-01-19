from django.utils.translation import gettext as _
from fhir.resources.identifier import Identifier
from fhir.resources.address import Address
from fhir.resources.extension import Extension
from fhir.resources.humanname import HumanName
from fhir.resources.organization import Organization

from api_fhir_r4.models.imisModelEnums import ContactPointSystem
from api_fhir_r4.configurations import R4IdentifierConfig, R4OrganisationConfig, GeneralConfiguration
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin


class InsuranceOrganisationConverter(BaseFHIRConverter):

    @classmethod
    def to_fhir_obj(cls, imis_organisation, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_organisation = Organization()
        imis_organisation = imis_organisation._cfg['insurer_organisation']
        cls.build_fhir_id(fhir_organisation, imis_organisation)
        cls.build_fhir_identifier_id(
            fhir_organisation,
            imis_organisation,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            cls.get_fhir_code_identifier_type()
        )
        cls.build_fhir_name(fhir_organisation, imis_organisation)
        cls.build_fhir_type(fhir_organisation, imis_organisation)
        cls.build_fhir_contact(fhir_organisation, imis_organisation)
        cls.build_fhir_telecom(fhir_organisation, imis_organisation)
        cls.build_fhir_address_organisation(fhir_organisation, imis_organisation)
        return fhir_organisation

    @classmethod
    def to_imis_obj(cls, fhir_organisation, audit_user_id):
        raise NotImplementedError(
            _('Insurance Organisation to_imis_obj() not implemented.')
        )

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

    @classmethod
    def get_fhir_resource_type(cls):
        return Organization

    @classmethod
    def build_fhir_id(cls, fhir_organisation, imis_organisation):
        fhir_organisation.id = f"{imis_organisation['fhir_insurer_organisation_id']}"

    @classmethod
    def build_fhir_identifier_id(cls, fhir_organisation, imis_organisation, type_system, type_code):
        fhir_organisation.identifier = []
        identifier = Identifier.construct()
        identifier.type = cls.build_codeable_concept(type_code, type_system)
        identifier.value = imis_organisation["fhir_insurer_organisation_code"]
        fhir_organisation.identifier.append(identifier)

    @classmethod
    def build_fhir_type(cls, fhir_organisation, imis_organisation):
        fhir_organisation.type = [cls.build_codeable_concept(
            code=imis_organisation["fhir_insurer_organisation_type"],
            system=R4OrganisationConfig.get_fhir_ph_organisation_type_system()
        )]

    @classmethod
    def build_fhir_name(cls, fhir_organisation, imis_organisation):
        fhir_organisation.name = imis_organisation["fhir_insurer_organisation_name"]

    @classmethod
    def build_fhir_telecom(cls, fhir_organisation, imis_organisation):
        fhir_organisation.telecom = []
        fhir_organisation.telecom.append(cls.build_fhir_contact_point(
            system=ContactPointSystem.EMAIL,
            value=imis_organisation["fhir_insurer_organisation_email"]))

        fhir_organisation.telecom.append(cls.build_fhir_contact_point(
            system=ContactPointSystem.FAX,
            value=imis_organisation["fhir_insurer_organisation_fax"]))

        fhir_organisation.telecom.append(cls.build_fhir_contact_point(
            system=ContactPointSystem.PHONE,
            value=imis_organisation["fhir_insurer_organisation_phone"]))

    @classmethod
    def build_fhir_contact(cls, fhir_organisation, imis_organisation):
        fhir_organisation.contact = []

        name = HumanName.construct()
        name.text = imis_organisation['fhir_insurer_organisation_contact_name']

        purpose = cls.build_codeable_concept(
            code="ADMIN",
            system=R4OrganisationConfig.get_fhir_ph_organisation_contactentity_type()
        )
        if len(purpose.coding) == 1:
            purpose.coding[0].display = _("Administrative")

        fhir_organisation.contact.append({'name': name, 'purpose': purpose})

    @classmethod
    def build_fhir_address_organisation(cls, fhir_organization, imis_organisation):
        addresses = []

        address = Address.construct()

        # municipality extension
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-municipality"
        extension.valueString = imis_organisation["fhir_insurer_organisation_municipality"]
        address.extension = [extension]

        address.line = [imis_organisation["fhir_insurer_organisation_line"]]
        address.state = imis_organisation["fhir_insurer_organisation_state"]
        address.district = imis_organisation["fhir_insurer_organisation_district"]
        address.city = imis_organisation["fhir_insurer_organisation_city"]

        addresses.append(address)
        fhir_organization.address = addresses