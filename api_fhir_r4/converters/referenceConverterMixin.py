import inspect

from api_fhir_r4.exceptions import FHIRRequestProcessException
from fhir.resources.reference import Reference

from api_fhir_r4.configurations import R4IdentifierConfig


class ReferenceConverterMixin(object):
    DB_ID_REFERENCE_TYPE = 'db_id_reference'
    UUID_REFERENCE_TYPE = 'uuid_reference'
    CODE_REFERENCE_TYPE = 'code_reference'

    @classmethod
    def get_reference_obj_uuid(cls, obj):
        raise NotImplementedError('`get_reference_obj_uuid()` must be implemented.')

    @classmethod
    def get_reference_obj_id(cls, obj):
        raise NotImplementedError('`get_reference_obj_id()` must be implemented.')

    @classmethod
    def get_reference_obj_code(cls, obj):
        raise NotImplementedError('`get_reference_obj_code()` must be implemented.')

    @classmethod
    def get_fhir_resource_type(cls):
        raise NotImplementedError('`get_fhir_resource_type()` must be implemented.')  # pragma: no cover

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        raise NotImplementedError('`get_imis_object_by_fhir_reference()` must be implemented.')  # pragma: no cover

    @classmethod
    def build_fhir_resource_reference(cls, obj, type=None, display=None, reference_type=UUID_REFERENCE_TYPE):
        reference = Reference.construct()

        resource_type = type if type else cls.__get_fhir_resource_type_as_string()
        resource_id = cls.__get_imis_object_id_as_string(obj, reference_type)

        reference.type = resource_type
        reference.identifier = cls.build_reference_identifier(obj, reference_type)
        reference.reference = resource_type + '/' + resource_id

        if display:
            reference.display = display

        return reference

    @classmethod
    def get_resource_id_from_reference(cls, reference):
        resource_id = None
        if reference:
            reference = reference.reference
            if isinstance(reference, str) and '/' in reference:
                path, resource_id = reference.rsplit('/', 1)
        if resource_id is None:
            raise FHIRRequestProcessException(['Could not fetch id from reference: {}'])
        return resource_id

    @classmethod
    def __get_imis_object_id_as_string(cls, obj, reference_type):
        if reference_type == cls.UUID_REFERENCE_TYPE:
            resource_id = cls.get_reference_obj_uuid(obj)
        elif reference_type == cls.DB_ID_REFERENCE_TYPE:
            resource_id = cls.get_reference_obj_id(obj)
        elif reference_type == cls.CODE_REFERENCE_TYPE:
            resource_id = cls.get_reference_obj_code(obj)
        else:
            raise FHIRRequestProcessException([f'Could not create reference for reference type {reference_type}'])

        if not isinstance(resource_id, str):
            resource_id = str(resource_id)
        return resource_id

    @classmethod
    def __get_fhir_resource_type_as_string(cls):
        resource_type = cls.get_fhir_resource_type()
        if inspect.isclass(resource_type):
            resource_type = resource_type.__name__
        if not isinstance(resource_type, str):
            resource_type = str(resource_type)
        return resource_type

    @classmethod
    def build_reference_identifier(cls, obj, reference_type):
        # Methods for building identifiers are expected to be implemented by classes derived BaseFHIRConverter
        identifiers = []
        if reference_type == cls.UUID_REFERENCE_TYPE:
            # If object is without uuid use id instead
            # If uuid is requested but not available id in simple string format is used
            if hasattr(obj, 'uuid'):
                cls.build_fhir_uuid_identifier(identifiers, obj)
            else:
                identifiers.append(str(obj.id))
        elif reference_type == cls.DB_ID_REFERENCE_TYPE:
            cls.build_fhir_id_identifier(identifiers, obj)
        elif reference_type == cls.CODE_REFERENCE_TYPE:
            cls.build_fhir_code_identifier(identifiers, obj)
        else:
            raise NotImplementedError(f"Unhandled reference type {reference_type}")

        return identifiers[0]
