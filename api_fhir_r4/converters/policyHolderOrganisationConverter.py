from urllib.parse import urljoin

from django.utils.translation import gettext as _
from fhir.resources.R4B.address import Address
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.humanname import HumanName

from api_fhir_r4.mapping.organizationMapping import (
    PolicyHolderOrganisationLegalFormMapping,
    PolicyHolderOrganisationActivityMapping,
)
from api_fhir_r4.models.imisModelEnums import (
    ImisLocationType,
    ContactPointSystem,
    AddressType,
)
from location.models import Location
from policyholder.models import PolicyHolder
from api_fhir_r4.configurations import (
    R4IdentifierConfig,
    R4OrganisationConfig,
    GeneralConfiguration,
)
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from fhir.resources.R4B.organization import Organization
from api_fhir_r4.utils import DbManagerUtils


class PolicyHolderOrganisationConverter(BaseFHIRConverter, ReferenceConverterMixin):
    @classmethod
    def to_fhir_obj(
        cls,
        imis_organisation,
        reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE,
    ):
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
        errors = []
        fhir_org = Organization(**fhir_organisation)
        imis_ph = PolicyHolder()
        imis_ph.audit_user_id = audit_user_id

        cls.build_imis_ph_identifier(imis_ph, fhir_org, errors)
        cls.build_imis_ph_name(imis_ph, fhir_org, errors)
        cls.build_imis_ph_legal_form(imis_ph, fhir_org, errors)
        cls.build_imis_ph_activity(imis_ph, fhir_org, errors)
        cls.build_imis_ph_telecom(imis_ph, fhir_org, errors)
        cls.build_imis_ph_address(imis_ph, fhir_org, errors)
        cls.build_imis_ph_contact(imis_ph, fhir_org, errors)

        cls.check_errors(errors)
        return imis_ph

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        return DbManagerUtils.get_object_or_none(
            PolicyHolder,
            **cls.get_database_query_id_parameteres_from_reference(reference)
        )

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
    def build_fhir_identifiers(
        cls, fhir_organisation, imis_organisation, reference_type
    ):
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
        codeable_concept = cls.build_codeable_concept_from_coding(
            cls.build_fhir_mapped_coding(
                PolicyHolderOrganisationLegalFormMapping.fhir_ph_code_system(
                    imis_organisation.legal_form
                )
            )
        )
        base = GeneralConfiguration.get_system_base_url()
        url = urljoin(
            base,
            R4OrganisationConfig.get_fhir_ph_organisation_legal_form_extension_system(),
        )
        extension = cls.build_fhir_codeable_concept_extension(codeable_concept, url)
        if isinstance(fhir_organisation.extension, list):
            fhir_organisation.extension.append(extension)
        else:
            fhir_organisation.extension = [extension]

    @classmethod
    def build_fhir_activity_extension(cls, fhir_organisation, imis_organisation):
        codeable_concept = cls.build_codeable_concept_from_coding(
            cls.build_fhir_mapped_coding(
                PolicyHolderOrganisationActivityMapping.fhir_ph_code_system(
                    imis_organisation.activity_code
                )
            )
        )
        base = GeneralConfiguration.get_system_base_url()
        url = urljoin(
            base,
            R4OrganisationConfig.get_fhir_ph_organisation_activity_extension_system(),
        )
        extension = cls.build_fhir_codeable_concept_extension(codeable_concept, url)
        if isinstance(fhir_organisation.extension, list):
            fhir_organisation.extension.append(extension)
        else:
            fhir_organisation.extension = [extension]

    @classmethod
    def build_fhir_type(cls, fhir_organisation):
        fhir_organisation.type = [
            cls.build_codeable_concept(
                R4OrganisationConfig.get_fhir_ph_organisation_type(),
                system=R4OrganisationConfig.get_fhir_ph_organisation_type_system(),
            )
        ]

    @classmethod
    def build_fhir_name(cls, fhir_organisation, imis_organisation):
        fhir_organisation.name = imis_organisation.trade_name

    @classmethod
    def build_fhir_telecom(cls, fhir_organisation, imis_organisation):
        fhir_organisation.telecom = []
        if imis_organisation.email:
            fhir_organisation.telecom.append(
                cls.build_fhir_contact_point(
                    system=ContactPointSystem.EMAIL, value=imis_organisation.email
                )
            )
        if imis_organisation.fax:
            fhir_organisation.telecom.append(
                cls.build_fhir_contact_point(
                    system=ContactPointSystem.FAX, value=imis_organisation.fax
                )
            )
        if imis_organisation.phone:
            fhir_organisation.telecom.append(
                cls.build_fhir_contact_point(
                    system=ContactPointSystem.PHONE, value=imis_organisation.phone
                )
            )

    @classmethod
    def build_fhir_ph_address(
        cls, fhir_organisation, imis_organisation, reference_type
    ):
        address = Address.construct()
        address.type = AddressType.PHYSICAL.value
        if imis_organisation.address and "address" in imis_organisation.address:
            address.line = [imis_organisation.address["address"]]
        fhir_organisation.address = [address]
        if imis_organisation.locations:
            cls.build_fhir_address_field(fhir_organisation, imis_organisation.locations)
            cls.build_fhir_location_extension(
                fhir_organisation, imis_organisation, reference_type
            )

    @classmethod
    def build_fhir_address_field(cls, fhir_organisation, location: Location):
        current_location = location
        while current_location:
            if current_location.type == ImisLocationType.REGION.value:
                fhir_organisation.address[0].state = current_location.name
            elif current_location.type == ImisLocationType.DISTRICT.value:
                fhir_organisation.address[0].district = current_location.name
            elif current_location.type == ImisLocationType.WARD.value:
                cls.build_fhir_municipality_extension(
                    fhir_organisation, current_location
                )
            elif current_location.type == ImisLocationType.VILLAGE.value:
                fhir_organisation.address[0].city = current_location.name
            current_location = current_location.parent

    @classmethod
    def build_fhir_municipality_extension(
        cls, fhir_organisation, municipality: Location
    ):
        extension = Extension.construct()
        base = GeneralConfiguration.get_system_base_url()
        extension.url = urljoin(
            base, R4OrganisationConfig.get_fhir_address_municipality_extension_system()
        )
        extension.valueString = municipality.name
        if isinstance(fhir_organisation.address[0].extension, list):
            fhir_organisation.address[0].extension.append(extension)
        else:
            fhir_organisation.address[0].extension = [extension]

    @classmethod
    def build_fhir_location_extension(
        cls, fhir_organisation, imis_organisation, reference_type
    ):
        base = GeneralConfiguration.get_system_base_url()
        url = urljoin(
            base, R4OrganisationConfig.get_fhir_location_reference_extension_system()
        )
        extension = cls.build_fhir_reference_extension(
            cls.build_fhir_resource_reference(
                imis_organisation.locations,
                type="Location",
                display=imis_organisation.locations.name,
                reference_type=reference_type,
            ),
            url,
        )
        if isinstance(fhir_organisation.address[0].extension, list):
            fhir_organisation.address[0].extension.append(extension)
        else:
            fhir_organisation.address[0].extension = [extension]

    @classmethod
    def build_fhir_contact(cls, fhir_organisation, imis_organisation):
        fhir_organisation.contact = []
        if imis_organisation.contact_name:
            name = HumanName.construct()
            name.text = "%s %s" % (
                imis_organisation.contact_name["name"],
                imis_organisation.contact_name["surname"],
            )
            fhir_organisation.contact.append({"name": name})

    @classmethod
    def build_imis_ph_identifier(cls, imis_ph, fhir_org, errors):
        value = cls.get_fhir_identifier_by_code(
            fhir_org.identifier, R4IdentifierConfig.get_fhir_generic_type_code()
        )
        if value:
            imis_ph.code = value
        cls.valid_condition(
            imis_ph.code is None, _("Missing PolicyHolder code"), errors
        )

    @classmethod
    def build_imis_ph_name(cls, imis_ph, fhir_org, errors):
        imis_ph.trade_name = fhir_org.name
        cls.valid_condition(
            imis_ph.trade_name is None, _("Missing PolicyHolder name"), errors
        )

    @classmethod
    def build_imis_ph_legal_form(cls, imis_ph, fhir_org, errors):
        if fhir_org.extension:
            ext_url_suffix = "organization-legal-form"
            legal_form_ext = next(
                (x for x in fhir_org.extension if ext_url_suffix in x.url), None
            )
            if legal_form_ext and hasattr(legal_form_ext, "valueCodeableConcept"):
                coding = cls.get_first_coding_from_codeable_concept(
                    legal_form_ext.valueCodeableConcept
                )
                if coding and coding.code:
                    imis_ph.legal_form = int(coding.code)

    @classmethod
    def build_imis_ph_activity(cls, imis_ph, fhir_org, errors):
        if fhir_org.extension:
            ext_url_suffix = "organization-activity"
            activity_ext = next(
                (x for x in fhir_org.extension if ext_url_suffix in x.url), None
            )
            if activity_ext and hasattr(activity_ext, "valueCodeableConcept"):
                coding = cls.get_first_coding_from_codeable_concept(
                    activity_ext.valueCodeableConcept
                )
                if coding and coding.code:
                    imis_ph.activity_code = int(coding.code)

    @classmethod
    def build_imis_ph_telecom(cls, imis_ph, fhir_org, errors):
        if fhir_org.telecom:
            for telecom in fhir_org.telecom:
                if telecom.system == ContactPointSystem.EMAIL.value:
                    imis_ph.email = telecom.value
                elif telecom.system == ContactPointSystem.PHONE.value:
                    imis_ph.phone = telecom.value
                elif telecom.system == ContactPointSystem.FAX.value:
                    imis_ph.fax = telecom.value

    @classmethod
    def build_imis_ph_address(cls, imis_ph, fhir_org, errors):
        if fhir_org.address and len(fhir_org.address) > 0:
            address = fhir_org.address[0]
            if address.line and len(address.line) > 0:
                imis_ph.address = {"address": address.line[0]}

    @classmethod
    def build_imis_ph_contact(cls, imis_ph, fhir_org, errors):
        if fhir_org.contact and len(fhir_org.contact) > 0:
            contact = fhir_org.contact[0]
            if hasattr(contact, "name") and contact.name:
                # Parse "FirstName LastName" format
                name_text = (
                    contact.name.text
                    if hasattr(contact.name, "text")
                    else str(contact.name)
                )
                name_parts = name_text.split(" ", 1)
                if len(name_parts) == 2:
                    imis_ph.contact_name = {
                        "name": name_parts[0],
                        "surname": name_parts[1],
                    }
                else:
                    imis_ph.contact_name = {"name": name_text, "surname": ""}
