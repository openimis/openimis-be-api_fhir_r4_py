from django.utils.translation import gettext
from insuree.models import Insuree, Gender, Education, Profession, Family
from location.models import Location
from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter,GroupConverterMixin, ReferenceConverterMixin
from fhir.resources.extension import Extension
from fhir.resources.group import Group
from api_fhir_r4.utils import DbManagerUtils
from api_fhir_r4.exceptions import FHIRException


class GroupConverter(BaseFHIRConverter, ReferenceConverterMixin, GroupConverterMixin):
    @classmethod
    def to_fhir_obj(cls, imis_family, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_family = {}
        # create two obligatory field then
        cls.build_fhir_actual(fhir_family, imis_family)
        cls.build_fhir_type(fhir_family, imis_family)
        fhir_family = Group(**fhir_family)
        # then create fhir object as usual
        cls.build_fhir_identifiers(fhir_family,imis_family)
        cls.build_fhir_pk(fhir_family, imis_family.uuid)
        cls.build_fhir_active(fhir_family,imis_family)
        cls.build_fhir_quantity(fhir_family,imis_family)
        cls.build_fhir_name(fhir_family,imis_family)
        # TODO - fix location and address according to FHIR requirements
        #cls.build_fhir_location(fhir_family,imis_family)
        #cls.build_fhir_addresses(fhir_family, imis_family)
        cls.build_fhir_member(fhir_family,imis_family)
        return fhir_family

    @classmethod
    def to_imis_obj(cls,fhir_family, audit_user_id):
        errors = []
        fhir_family = Group(**fhir_family)
        imis_family = Family()
        imis_family.audit_user_id = audit_user_id
        cls.build_imis_location(imis_family,fhir_family)
        cls.build_imis_head(imis_family,fhir_family,errors)
        cls.check_errors(errors)
        return imis_family

    @classmethod
    def get_reference_obj_id(cls, imis_family):
        return imis_family.uuid

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
        if not cls.valid_condition(members is None, gettext('Missing `member` attribute'),errors):
            if len(members) ==0:
                members = None
                cls.valid_condition(members is None, gettext('Missing member should not be empty'), errors)
            for member in members:
                cls.build_imis_identifiers(imis_family,member.entity.identifier)
      
    @classmethod
    def build_head(cls,identifier,lookup_code):
        value = None
        first_coding = cls.get_first_coding_from_codeable_concept(identifier.type)
        if first_coding.system == R4IdentifierConfig.get_fhir_identifier_type_system() and first_coding.code == lookup_code:
                value = identifier.value
        return value
        
    @classmethod
    def build_fhir_identifiers(cls, fhir_family, imis_family):
        identifiers = []
        cls.build_fhir_uuid_identifier(identifiers, imis_family)
        fhir_family.identifier = identifiers

    @classmethod
    def build_imis_identifiers(cls, imis_family,identifier):
        value = cls.build_head(identifier,R4IdentifierConfig.get_fhir_chfid_type_code())
        if value:
            try:
                imis_family.head_insuree = Insuree.objects.get(chf_id=value)
            except:
                raise FHIRException('Invalid insuree chf_id')

    @classmethod
    def build_imis_location(cls, imis_family,fhir_family):
        if fhir_family.location.name is not None:
            try:
                location = Location.objects.get(name=fhir_family.location.name)
                fhir_family.location = location
            except:
                raise FHIRException('Invalid location')

    @classmethod
    def build_fhir_name(cls, fhir_family, imis_family):
      if imis_family.head_insuree is not None:
          fhir_family.name = imis_family.head_insuree.last_name
    
    @classmethod
    def build_fhir_actual(cls, fhir_family, imis_family):
        fhir_family['actual'] = True
    
    @classmethod
    def build_fhir_type(cls, fhir_family, imis_family):
        fhir_family['type'] = "Person"
        
    @classmethod
    def build_fhir_active(cls, fhir_family, imis_family):
        fhir_family.active =True
    
    
    @classmethod
    def build_fhir_member(cls,fhir_family,imis_family):
        fhir_family.member = cls.build_fhir_members(imis_family.uuid)

    @classmethod
    def build_fhir_quantity(cls,fhir_family,imis_family):
        quantity=Insuree.objects.filter(family__uuid=imis_family.uuid).count()
        fhir_family.quantity=quantity
        
    @classmethod
    def build_fhir_addresses(cls, fhir_family, imis_family):
        addresses = []
        if imis_family.address is not None:
            current_address = cls.build_fhir_address(imis_family.address, "home",
                                                     "physical")
            addresses.append(current_address)
        if type(fhir_family.address) is not list:
            fhir_family.address = addresses
        else:
            fhir_family.address.append(addresses)

    @classmethod
    def build_imis_addresses(cls, imis_family, fhir_family):
        addresses = fhir_family.address
        if addresses is not None:
            for address in addresses:
                if address.type == "physical":
                    imis_family.current_address = address.text
                elif address.type == "both":
                    imis_family.geolocation = address.text

    @classmethod
    def build_poverty_status(cls, fhir_family, imis_family):
        poverty_status = cls.build_poverty_status_extension(imis_family)
        if poverty_status.valueBoolean is not None:
            if type(fhir_family.extension) is not list:
                fhir_family.extension = poverty_status
            else:
                fhir_family.extension.append(poverty_status)

    @classmethod
    def build_poverty_status_extension(cls, imis_family):
        extension = Extension.construct()
        extension.url = "https://openimis.atlassian.net/wiki/spaces/OP/pages/1556643849/povertyStatus"
        extension.valueBoolean = imis_family.family.poverty
        return extension

   