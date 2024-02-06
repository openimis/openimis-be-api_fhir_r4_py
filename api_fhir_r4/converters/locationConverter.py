from django.utils.translation import gettext as _
from django.utils.translation import gettext
from location.models import Location

from api_fhir_r4.configurations import R4IdentifierConfig, R4LocationConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from fhir.resources.R4B.location import Location as FHIRLocation

from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.mapping.locationMapping import LocationTypeMapping
from api_fhir_r4.utils import DbManagerUtils


class LocationConverter(BaseFHIRConverter, ReferenceConverterMixin):
    PHYSICAL_TYPES = LocationTypeMapping.PHYSICAL_TYPES_DEFINITIONS

    @classmethod
    def to_fhir_obj(cls, imis_location, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_location = FHIRLocation.construct()
        cls.build_fhir_physical_type(fhir_location, imis_location)
        cls.build_fhir_pk(fhir_location, imis_location, reference_type)
        cls.build_fhir_location_identifier(fhir_location, imis_location)
        cls.build_fhir_location_name(fhir_location, imis_location)
        cls.build_fhir_part_of(fhir_location, imis_location, reference_type)
        cls.build_fhir_status(fhir_location, imis_location)
        cls.build_fhir_mode(fhir_location)
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
        return DbManagerUtils.get_object_or_none(Location, **cls.get_database_query_id_parameteres_from_reference(reference))

    @classmethod
    def build_fhir_location_identifier(cls, fhir_location, imis_location):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_location)
        fhir_location.identifier = identifiers
        cls._validate_imis_identifiers(identifiers)

    @classmethod
    def build_fhir_location_code_identifier(cls, identifiers, imis_location):
        if imis_location is not None:
            identifier = cls.build_fhir_identifier(imis_location.code,
                                                   R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                   R4IdentifierConfig.get_fhir_location_code_type())
            identifiers.append(identifier)

    @classmethod
    def build_imis_location_identiftier(cls, imis_location, fhir_location, errors):
        value = cls.get_fhir_identifier_by_code(
            fhir_location.identifier,
            R4IdentifierConfig.get_fhir_location_code_type()
        )
        if value:
            imis_location.code = value
        cls.valid_condition(imis_location.code is None, gettext('Missing location code'), errors)

    @classmethod
    def build_fhir_location_name(cls, fhir_location, imis_location):
        fhir_location.name = imis_location.name
        cls._validate_imis_name(imis_location)

    @classmethod
    def build_imis_location_name(cls, imis_location, fhir_location, errors):
        name = fhir_location.name
        if not cls.valid_condition(name is None, _('Missing location `name` attribute'), errors):
            imis_location.name = name

    @classmethod
    def build_fhir_physical_type(cls, fhir_location, imis_location):
        cls._validate_physical_type(imis_location)
        system_definition = cls.PHYSICAL_TYPES.get(imis_location.type)
        fhir_location.physicalType = cls.build_codeable_concept(**system_definition)

    @classmethod
    def build_imis_location_type(cls, imis_location, fhir_location, errors):
        code = None
        try:
            code = fhir_location.physicalType.coding[0].code
            imis_code = next(
                (k for k, v in cls.PHYSICAL_TYPES.items() if v['code'] == code), None
            )
            imis_location.type = imis_code
            cls._validate_physical_type(imis_location)

        except KeyError:
            errors.append(_('Missing location physical type'))
        except FHIRException:
            errors.append(
                _('Invalid location physical type with code %(code), allowed codes are: %(types)') % {
                    'code': code,
                    'types': [v['code'] for v in cls.PHYSICAL_TYPES.values]
                }
            )

    @classmethod
    def build_fhir_part_of(cls, fhir_location, imis_location, reference_type):
        if not cls.__is_highers_level_location(imis_location):
            fhir_location.partOf = LocationConverter.build_fhir_resource_reference(
                imis_location.parent,
                'Location',
                imis_location.parent.code,
                reference_type=reference_type
            )

    def get_location_from_address(cls, fhir_patient_address):
        location_reference_ext = next((
            ext for ext in fhir_patient_address.extension if 'address-location-reference' in ext.url
        ))
        location =  cls.get_imis_obj_by_fhir_reference(location_reference_ext.valueReference)
        if location is None and location_reference_ext:
            raise FHIRException(f"Invalid location reference, {location_reference_ext.valueReference} doesn't match any location.")
        if location is None:
            matching_locations = Location.objects \
                .filter(
                    validity_to__isnull=True,
                    name=address.district,
                    parent__name=address.state,
                    type="D"  # HF is expected to be at district level
                ).distinct()\
                .all()
        
            if matching_locations.count() != 1:
                raise FHIRException(cls.__get_invalid_location_msg(address, matching_locations))
            else:
                location = matching_locations.first()
        return location
    
    
    @classmethod
    def __get_invalid_location_msg(cls, address, matching_locations):
        count = matching_locations.count()
        if count == 0:
            return _(F"No matching location for district {address.district}, state {address.state}.")
        elif count > 1:
            return _(F"More than one matching location district {address.district}, state {address.state}:\n"
                     F"{matching_locations}.")

    @classmethod
    def build_imis_parent_location_id(cls, imis_location, fhir_location, errors):
        if fhir_location.partOf:
            resource = cls.get_imis_obj_by_fhir_reference(fhir_location.partOf) 
            if not resource:
                errors.append(
                    _('Invalid Location\'s partOf.reference')
                )


    @classmethod
    def _validate_imis_identifiers(cls, identifiers):
        code_identifier = cls.get_fhir_identifier_by_code(identifiers, cls.get_fhir_code_identifier_type())
        if not code_identifier:
            raise FHIRException(_('Code identifier has to be present in FHIR Location identifiers, '
                                  '\nidentifiers are: %(identifiers)') % {'identifiers': identifiers})

    @classmethod
    def _validate_imis_name(cls, imis_location):
        if not imis_location.name:
            raise FHIRException(
                _('Location  %(location_uuid)s without name') % {'uuid': imis_location.uuid}
            )

    @classmethod
    def _validate_physical_type(cls, imis_location):
        allowed_keys = cls.PHYSICAL_TYPES.keys()
        if not imis_location or (imis_location.type not in allowed_keys):
            
            error_msg_keys = {
                'type': imis_location.type, 'location': imis_location.uuid, 'types': allowed_keys
            } if imis_location else {'type':None,'location':None,'types': allowed_keys}
            raise FHIRException(
                _('Invalid Location\'s type %(type) for location %(location), '
                  'supported types are: %(types)') % error_msg_keys
            )

    @classmethod
    def build_fhir_mode(cls, fhir_location):
        fhir_location.mode = 'instance'

    @classmethod
    def build_fhir_status(cls, fhir_location, imis_location):
        if cls.__location_active(imis_location):
            fhir_location.status = R4LocationConfig.get_fhir_code_for_active()
        else:
            fhir_location.status = R4LocationConfig.get_fhir_code_for_inactive()

    @classmethod
    def __location_active(cls, imis_location):
        return imis_location.validity_to is None

    @classmethod
    def __is_highers_level_location(cls, imis_location):
        return imis_location.parent is None

    @classmethod
    def _is_code_reference(cls, location_part_of):
        if location_part_of.identifier:
            try:
                ref_type_code = location_part_of.identifier.type.coding[0].code
                return ref_type_code == R4IdentifierConfig.get_fhir_location_code_type()
            except KeyError:
                raise FHIRException(_("Invalid format for Location's partOf identifier."))
        else:
            # Default expected reference identifier is uuid
            return False
