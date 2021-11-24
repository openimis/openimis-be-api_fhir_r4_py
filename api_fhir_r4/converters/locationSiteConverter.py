from django.utils.translation import gettext
from location.models import HealthFacility
from api_fhir_r4.configurations import R4IdentifierConfig, R4LocationConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from fhir.resources.location import Location as FHIRLocation
from api_fhir_r4.models.imisModelEnums import ImisHfLevel
from api_fhir_r4.utils import DbManagerUtils


class LocationSiteConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_hf, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_location = FHIRLocation.construct()
        cls.build_fhir_physical_type(fhir_location, imis_hf)
        cls.build_fhir_pk(fhir_location, imis_hf, reference_type)
        cls.build_fhir_location_identifier(fhir_location, imis_hf)
        cls.build_fhir_location_name(fhir_location, imis_hf)
        cls.build_fhir_type(fhir_location, imis_hf)
        cls.build_fhir_part_of(fhir_location, imis_hf, reference_type)
        cls.mode = 'instance'
        return fhir_location

    @classmethod
    def to_imis_obj(cls, fhir_location, audit_user_id):
        errors = []
        fhir_location = FHIRLocation(**fhir_location)
        imis_hf = HealthFacility() 
        cls.build_imis_hf_identiftier(imis_hf, fhir_location, errors)
        cls.build_imis_hf_name(imis_hf, fhir_location, errors)
        cls.build_imis_hf_level(imis_hf, fhir_location, errors)
        cls.build_imis_parent_location_id(imis_hf, fhir_location, errors)            
        cls.check_errors(errors)
        return imis_hf

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_facility_id_type()

    @classmethod
    def get_reference_obj_uuid(cls, imis_hf: HealthFacility):
        return imis_hf.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_hf: HealthFacility):
        return imis_hf.id

    @classmethod
    def get_reference_obj_code(cls, imis_hf: HealthFacility):
        return imis_hf.code


    @classmethod
    def get_fhir_resource_type(cls):
        return FHIRLocation

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        location_uuid = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(HealthFacility, uuid=location_uuid)

    @classmethod
    def build_fhir_location_identifier(cls, fhir_location, imis_hf):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_hf)
        fhir_location.identifier = identifiers

    @classmethod
    def build_fhir_location_code_identifier(cls, identifiers, imis_hf):
        if imis_hf is not None:
            identifier = cls.build_fhir_identifier(imis_hf.code,
                                                   R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                   R4IdentifierConfig.get_fhir_facility_id_type())
            identifiers.append(identifier)

    @classmethod
    def build_imis_hf_identiftier(cls, imis_hf, fhir_location, errors):
        value = cls.get_fhir_identifier_by_code(fhir_location.identifier,
                                                R4IdentifierConfig.get_fhir_facility_id_type())
        if value:
            imis_hf.code = value
        cls.valid_condition(imis_hf.code is None, gettext('Missing location code'), errors)

    @classmethod
    def build_fhir_location_name(cls, fhir_location, imis_hf):
        fhir_location.name = imis_hf.name

    @classmethod
    def build_imis_hf_name(cls, imis_hf, fhir_location, errors):
        name = fhir_location.name
        if not cls.valid_condition(name is None,
                                   gettext('Missing location `name` attribute'), errors):
            imis_hf.name = name

    @classmethod
    def build_fhir_physical_type(cls, fhir_location, imis_hf):
        code = R4LocationConfig.get_fhir_code_for_site()
        text = "site"
        fhir_location.physicalType = \
            cls.build_codeable_concept(code, R4LocationConfig.get_fhir_location_physical_type_system(), text=text)

    @classmethod
    def build_fhir_type(cls, fhir_location, imis_hf):
        code = ""
        text = ""
        if imis_hf.level == ImisHfLevel.HEALTH_CENTER.value:
            code = R4LocationConfig.get_fhir_code_for_health_center()
            text = "health-center"
        elif imis_hf.level == ImisHfLevel.DISPENSARY.value:
            code = R4LocationConfig.get_fhir_code_for_dispensary()
            text = "dispensary"
        elif imis_hf.level == ImisHfLevel.HOSPITAL.value:
            code = R4LocationConfig.get_fhir_code_for_hospital()
            text = "hospital"
        fhir_location.type = \
            [cls.build_codeable_concept(code, R4LocationConfig.get_fhir_location_site_type_system(), text=text)]

    @classmethod
    def build_imis_hf_level(cls, imis_hf, fhir_location, errors):
        code = fhir_location.type[0].coding[0].code
        if code == R4LocationConfig.get_fhir_code_for_hospital():
            imis_hf.level = ImisHfLevel.HOSPITAL.value
        elif code == R4LocationConfig.get_fhir_code_for_dispensary():
            imis_hf.level = ImisHfLevel.DISPENSARY.value
        elif code == R4LocationConfig.get_fhir_code_for_health_center():
            imis_hf.level = ImisHfLevel.HEALTH_CENTER.value
        cls.valid_condition(imis_hf.level is None, gettext('Missing location level'), errors)

    @classmethod
    def build_fhir_part_of(cls, fhir_location, imis_hf, reference_type):
        if imis_hf.location is not None:
            fhir_location.partOf = \
                LocationSiteConverter.build_fhir_resource_reference(
                    imis_hf.location,
                    'Location',
                    imis_hf.location.code,
                    reference_type)

    @classmethod
    def build_imis_parent_location_id(cls, imis_hf, fhir_location, errors):
        if fhir_location.partOf:
            parent_id = fhir_location.partOf
            if not cls.valid_condition(parent_id is None,
                                       gettext('Missing location `parent id` attribute'), errors):
                # get the imis location object, check if exists
                uuid_location = parent_id.identifier.value
                hf_location = Location.objects.filter(uuid=uuid_location)
                if hf_location:
                    hf_location = hf_location.first()
                    imis_hf.location = hf_location
