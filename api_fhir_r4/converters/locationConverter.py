from django.utils.translation import gettext
from location.models import Location

from api_fhir_r4.configurations import R4IdentifierConfig, R4LocationConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from fhir.resources.location import Location as FHIRLocation
from api_fhir_r4.models.imisModelEnums import ImisLocationType
from api_fhir_r4.utils import DbManagerUtils


class LocationConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_location, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_location = FHIRLocation.construct()
        cls.build_fhir_physical_type(fhir_location, imis_location)
        cls.build_fhir_pk(fhir_location, imis_location, reference_type)
        cls.build_fhir_location_identifier(fhir_location, imis_location)
        cls.build_fhir_location_name(fhir_location, imis_location)
        cls.build_fhir_type(fhir_location, imis_location)
        cls.build_fhir_part_of(fhir_location, imis_location, reference_type)
        cls.mode = 'instance'
        return fhir_location

    @classmethod
    def to_imis_obj(cls, fhir_location, audit_user_id):
        errors = []
        fhir_location = FHIRLocation(**fhir_location)
        imis_location = Location()
        cls.build_imis_location_identiftier(imis_location, fhir_location, errors)
        cls.build_imis_location_name(imis_location, fhir_location, errors)
        cls.build_imis_location_type(imis_location, fhir_location, errors)
        cls.build_imis_parent_location_id(imis_location, fhir_location, errors)
        cls.check_errors(errors)
        return imis_location

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_location_code_type()

    @classmethod
    def get_reference_obj_uuid(cls, imis_location: Location):
        return imis_location.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_location: Location):
        return imis_location.id

    @classmethod
    def get_reference_obj_code(cls, imis_location: Location):
        return imis_location.code


    @classmethod
    def get_fhir_resource_type(cls):
        return Location

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        location_uuid = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Location, uuid=location_uuid)

    @classmethod
    def build_fhir_location_identifier(cls, fhir_location, imis_location):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_location)
        fhir_location.identifier = identifiers

    @classmethod
    def build_fhir_location_code_identifier(cls, identifiers, imis_location):
        if imis_location is not None:
            identifier = cls.build_fhir_identifier(imis_location.code,
                                                   R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                   R4IdentifierConfig.get_fhir_location_code_type())
            identifiers.append(identifier)

    @classmethod
    def build_imis_location_identiftier(cls, imis_location, fhir_location, errors):
        value = cls.get_fhir_identifier_by_code(fhir_location.identifier,
                                                R4IdentifierConfig.get_fhir_location_code_type())
        if value:
            imis_location.code = value
        cls.valid_condition(imis_location.code is None, gettext('Missing location code'), errors)

    @classmethod
    def build_fhir_location_name(cls, fhir_location, imis_location):
        fhir_location.name = imis_location.name

    @classmethod
    def build_imis_location_name(cls, imis_location, fhir_location, errors):
        name = fhir_location.name
        if not cls.valid_condition(name is None,
                                   gettext('Missing location `name` attribute'), errors):
            imis_location.name = name

    @classmethod
    def build_fhir_physical_type(cls, fhir_location, imis_location):
        code = R4LocationConfig.get_fhir_code_for_area()
        text = "Area"
        fhir_location.physicalType = \
            cls.build_codeable_concept(code, R4LocationConfig.get_fhir_location_physical_type_system(), text=text)

    @classmethod
    def build_fhir_type(cls, fhir_location, imis_location):
        code = ""
        text = ""
        if imis_location.type == ImisLocationType.REGION.value:
            code = R4LocationConfig.get_fhir_code_for_region()
            text = "region"
        elif imis_location.type == ImisLocationType.DISTRICT.value:
            code = R4LocationConfig.get_fhir_code_for_district()
            text = "district"
        elif imis_location.type == ImisLocationType.WARD.value:
            code = R4LocationConfig.get_fhir_code_for_ward()
            text = "ward"
        elif imis_location.type == ImisLocationType.VILLAGE.value:
            code = R4LocationConfig.get_fhir_code_for_village()
            text = "village"
            
        fhir_location.type = \
            [cls.build_codeable_concept(code, R4LocationConfig.get_fhir_location_area_type_system(), text=text)]
        

    @classmethod
    def build_imis_location_type(cls, imis_location, fhir_location, errors):
        # get the type of location code
        code = fhir_location.type[0].coding[0].code
        if code == R4LocationConfig.get_fhir_code_for_region():
            imis_location.type = ImisLocationType.REGION.value
        elif code == R4LocationConfig.get_fhir_code_for_district():
            imis_location.type = ImisLocationType.DISTRICT.value
        elif code == R4LocationConfig.get_fhir_code_for_ward():
            imis_location.type = ImisLocationType.WARD.value
        elif code == R4LocationConfig.get_fhir_code_for_village():
            imis_location.type = ImisLocationType.VILLAGE.value
        cls.valid_condition(imis_location.type is None, gettext('Missing location type'), errors)

    @classmethod
    def build_fhir_part_of(cls, fhir_location, imis_location, reference_type):
        partOf = None
        if imis_location.parent is not None:
            fhir_location.partOf = LocationConverter.build_fhir_resource_reference(
                imis_location.parent, 'Location', imis_location.parent.code, reference_type=reference_type)

    @classmethod
    def build_imis_parent_location_id(cls, imis_location, fhir_location, errors):
        if fhir_location.partOf:
            parent_id = fhir_location.partOf
            if not cls.valid_condition(parent_id is None,
                                       gettext('Missing location `parent id` attribute'), errors):

                # get the imis parent location object, check if exists
                uuid_location = parent_id.identifier.value
                parent_location = Location.objects.filter(uuid=uuid_location)
                if parent_location:
                    parent_location = parent_location.first()
                    imis_location.parent = parent_location
