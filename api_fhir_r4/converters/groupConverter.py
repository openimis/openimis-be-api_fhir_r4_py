from django.db.models.query import Q
from django.utils.translation import gettext as _
from insuree.models import Insuree, InsureePolicy, Family, FamilyType, ConfirmationType
from policy.models import Policy
from location.models import Location
from api_fhir_r4.configurations import R4IdentifierConfig, GeneralConfiguration
from api_fhir_r4.converters import BaseFHIRConverter, GroupConverterMixin, ReferenceConverterMixin
from api_fhir_r4.converters.locationConverter import LocationConverter
from api_fhir_r4.mapping.groupMapping import GroupTypeMapping, ConfirmationTypeMapping
from fhir.resources.extension import Extension
from fhir.resources.group import Group
from api_fhir_r4.utils import DbManagerUtils
from api_fhir_r4.exceptions import FHIRException


class GroupConverter(BaseFHIRConverter, ReferenceConverterMixin, GroupConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_family, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_family = {}
        # create two obligatory field
        cls.build_fhir_actual(fhir_family, imis_family)
        cls.build_fhir_type(fhir_family, imis_family)
        fhir_family = Group(**fhir_family)
        # then create fhir object as usual
        cls.build_fhir_extentions(fhir_family, imis_family, reference_type)
        cls.build_fhir_identifiers(fhir_family, imis_family)
        cls.build_fhir_pk(fhir_family, imis_family, reference_type=reference_type)
        cls.build_fhir_active(fhir_family, imis_family)
        cls.build_fhir_quantity(fhir_family, imis_family)
        cls.build_fhir_name(fhir_family, imis_family)
        cls.build_fhir_member(fhir_family, imis_family)
        return fhir_family

    @classmethod
    def to_imis_obj(cls, fhir_family, audit_user_id):
        errors = []
        fhir_family = Group(**fhir_family)
        imis_family = Family()
        # set uuid to Null so as to use this family object properly in service
        imis_family.uuid = None
        imis_family.audit_user_id = audit_user_id
        cls.build_imis_head(imis_family, fhir_family, errors)
        cls.build_imis_extentions(imis_family, fhir_family)
        cls.check_errors(errors)
        return imis_family

    @classmethod
    def get_reference_obj_id(cls, imis_family):
        return imis_family.id

    @classmethod
    def get_fhir_resource_type(cls):
        return Group

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_family_uuid = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Insuree, uuid=imis_family_uuid)

    @classmethod
    def build_human_names(cls,fhir_family, imis_family):
        name = cls.build_fhir_names_for_person(imis_family)
        if type(fhir_family.head) is not list:
            fhir_family.head = [name]
        else:
            fhir_family.head.append(name)

    @classmethod
    def build_imis_head(cls, imis_family, fhir_family, errors):
        members = fhir_family.member
        if not cls.valid_condition(members is None, _('Missing `member` attribute'), errors):
            if len(members) == 0:
                members = None
                cls.valid_condition(members is None, _('Missing member should not be empty'), errors)
            for member in members:
                cls.build_imis_identifiers(imis_family, member.entity.reference)
        
    @classmethod
    def build_fhir_identifiers(cls, fhir_family, imis_family):
        identifiers = []
        cls.build_fhir_uuid_identifier(identifiers, imis_family)
        cls.build_fhir_code_identifier(identifiers, imis_family)
        fhir_family.identifier = identifiers
        cls._validate_fhir_identifier_is_exist(fhir_family)

    @classmethod
    def build_fhir_code_identifier(cls, identifiers, imis_family):
        cls._build_family_head_identifier(identifiers, imis_family)

    @classmethod
    def _build_family_head_identifier(cls, identifiers, imis_family):
        cls._validate_imis_identifier_code(imis_family)
        head_id = cls.build_fhir_identifier(
            imis_family.head_insuree.chf_id,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        identifiers.append(head_id)

    @classmethod
    def build_imis_identifiers(cls, imis_family, reference):
        cls._validate_fhir_family_identifier_code(reference)
        value = reference.split('/')[-1]
        try:
            imis_family.head_insuree = Insuree.objects.get(chf_id=value, validity_to__isnull=True)
        except:
            raise FHIRException(
                _('Such insuree %(chf_id)s does not exist') % {'chf_id': value}
            )

    @classmethod
    def build_fhir_name(cls, fhir_family, imis_family):
      if imis_family.head_insuree is not None:
          fhir_family.name = imis_family.head_insuree.last_name
    
    @classmethod
    def build_fhir_actual(cls, fhir_family, imis_family):
        fhir_family['actual'] = True
    
    @classmethod
    def build_fhir_type(cls, fhir_family, imis_family):
        # according to the IMIS profile - always 'Person' value
        fhir_family['type'] = "Person"
        
    @classmethod
    def build_fhir_active(cls, fhir_family, imis_family):
        number_of_active_policy = InsureePolicy.objects.filter(
            Q(insuree__family__uuid=imis_family.uuid),
            Q(policy__status=Policy.STATUS_ACTIVE),
            Q(validity_to__isnull=True)
        ).count()
        fhir_family.active = True if number_of_active_policy > 0 else False

    @classmethod
    def build_fhir_member(cls,fhir_family, imis_family):
        fhir_family.member = cls.build_fhir_members(imis_family.uuid)

    @classmethod
    def build_fhir_quantity(cls,fhir_family, imis_family):
        quantity = Insuree.objects.filter(family__uuid=imis_family.uuid, validity_to__isnull=True).count()
        fhir_family.quantity = quantity

    @classmethod
    def build_fhir_extentions(cls, fhir_family, imis_family, reference_type):
        fhir_family.extension = []

        def build_extension(fhir_family, imis_family, value):
            extension = Extension.construct()
            if value == "group-address":
                cls._build_extension_address(extension, fhir_family, imis_family, reference_type=reference_type)

            elif value == "group-poverty-status":
                extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-poverty-status"
                extension.valueBoolean = imis_family.poverty

            elif value == "group-type":
                extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-type"
                if hasattr(imis_family, "family_type") and imis_family.family_type is not None:
                    display = GroupTypeMapping.group_type[str(imis_family.family_type.code)]
                    system = "CodeSystem/group-types"
                    extension.valueCodeableConcept = cls.build_codeable_concept(code=str(imis_family.family_type.code),
                                                                                system=system)
                    if len(extension.valueCodeableConcept.coding) == 1:
                        extension.valueCodeableConcept.coding[0].display = display
            # group-confirmation
            else:
                cls._build_extension_group_confirmation(extension, fhir_family, imis_family)

            if type(fhir_family.extension) is not list:
                fhir_family.extension = [extension]
            else:
                fhir_family.extension.append(extension)

        # check if family has location
        cls._validate_imis_family_location(imis_family)
        build_extension(fhir_family, imis_family, "group-address")
        if imis_family.poverty is not None:
            build_extension(fhir_family, imis_family, "group-poverty-status")
        if imis_family.family_type is not None:
            build_extension(fhir_family, imis_family, "group-type")
        if imis_family.confirmation_type is not None and imis_family.confirmation_no is not None:
            build_extension(fhir_family, imis_family, "group-confirmation")

    @classmethod
    def build_imis_extentions(cls, imis_family, fhir_family):
        cls._validate_fhir_extension_is_exist(fhir_family)
        for extension in fhir_family.extension:
            if extension.url == f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-address":
                address = extension.valueAddress
                if address:
                    # insuree use temp address
                    if address.use == "home":
                        if address.type == "physical":
                            imis_family.address = address.text
                            for ext in address.extension:
                                if "StructureDefinition/address-location-reference" in ext.url:
                                    value = cls.get_location_reference(ext.valueReference.reference)
                                    if value:
                                        try:
                                            imis_family.location = Location.objects.get(uuid=value, validity_to__isnull=True)
                                        except:
                                            imis_family.location = None

            elif extension.url == f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-poverty-status":
                imis_family.poverty = extension.valueBoolean

            elif extension.url == f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-type":
                try:
                    imis_family.family_type = FamilyType.objects.get(code=extension.valueCodeableConcept.coding[0].code)
                except:
                    imis_family.family_type = None

            elif extension.url == f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-confirmation":
                try:
                    for ext in extension.extension:
                        if ext.url == "number":
                            fhir_family.confirmation_no = ext.valueString
                        if ext.url == "type":
                            fhir_family.confirmation_type = ConfirmationType.objects.get(
                                code=ext.valueCodeableConcept.coding[0].code)
                except:
                    imis_family.confirmation_no = None
                    imis_family.confirmation_type = None
            else:
                pass
        cls._validate_imis_family_location(imis_family)

    @classmethod
    def get_location_reference(cls, location):
        return location.rsplit('Location/', 1)[1]

    @classmethod
    def _build_extension_address(cls, extension, fhir_family, imis_family, reference_type):
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-address"
        family_address = cls.build_fhir_address(imis_family.address, "home", "physical")
        if imis_family.location:
            family_address.state = imis_family.location.parent.parent.parent.name
            family_address.district = imis_family.location.parent.parent.name
            # municipality extension
            extension_address = Extension.construct()
            extension_address.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-municipality"
            extension_address.valueString = imis_family.location.parent.name
            family_address.extension = [extension_address]

            # address location reference extension
            extension_address = Extension.construct()
            extension_address.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-location-reference"
            extension_address.valueReference = LocationConverter\
                .build_fhir_resource_reference(imis_family.location, 'Location', reference_type=reference_type)
            family_address.extension.append(extension_address)
            family_address.city = imis_family.location.name
        extension.valueAddress = family_address

    @classmethod
    def _build_extension_group_confirmation(cls, extension, fhir_family, imis_family):
        nested_extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-confirmation"
        if hasattr(imis_family, "confirmation_type") and imis_family.confirmation_type:
            if hasattr(imis_family, "confirmation_no") and imis_family.confirmation_no:
                # add number extension
                nested_extension.url = "number"
                nested_extension.valueString = imis_family.confirmation_no
                extension.extension = [nested_extension]
                # add identifier extension
                nested_extension = Extension.construct()
                nested_extension.url = "type"
                system = "CodeSystem/group-confirmation-type"
                display = ConfirmationTypeMapping.confirmation_type[str(imis_family.confirmation_type.code)]
                nested_extension.valueCodeableConcept = cls.build_codeable_concept(
                    code=imis_family.confirmation_type.code, system=system)
                if len(nested_extension.valueCodeableConcept.coding) == 1:
                    nested_extension.valueCodeableConcept.coding[0].display = display
                extension.extension.append(nested_extension)

    @classmethod
    def get_reference_obj_uuid(cls, imis_family: Family):
        return imis_family.uuid

    # fhir validations
    @classmethod
    def _validate_fhir_identifier_is_exist(cls, fhir_family):
        if not fhir_family.identifier or len(fhir_family.identifier) == 0:
            raise FHIRException(
                _('FHIR Group entity without identifier')
            )

    # fhir validations
    @classmethod
    def _validate_fhir_extension_is_exist(cls, fhir_family):
        if not fhir_family.extension or len(fhir_family.extension) == 0:
            raise FHIRException(
                _('At least one extension with address is required')
            )

    @classmethod
    def _validate_fhir_family_identifier_code(cls, fhir_family_identifier_code):
        if not fhir_family_identifier_code:
            raise FHIRException(
                _('Family Group FHIR without code - this field is obligatory')
            )

    # imis validations
    @classmethod
    def _validate_imis_identifier_code(cls, imis_family):
        if not imis_family.head_insuree.chf_id:
            raise FHIRException(
                _('Family %(family_uuid)s without code') % {'family_uuid': imis_family.uuid}
            )

    @classmethod
    def _validate_imis_family_location(cls, imis_family):
        if not imis_family.location:
            if imis_family.uuid:
                raise FHIRException(
                    _('Family %(family_uuid)s without location') % {'family_uuid': imis_family.uuid}
                )
            else:
                raise FHIRException(
                    _('new Family without location')
                )
