import inspect
import logging

from typing import Tuple
import uuid
from api_fhir_r4.exceptions import FHIRRequestProcessException
from fhir.resources.R4B.reference import Reference


logger = logging.getLogger(__name__)


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
        if obj:
            reference = Reference.construct()

            resource_type = type if type else cls.__get_fhir_resource_type_as_string()
            resource_id = cls.__get_imis_object_id_as_string(obj, reference_type)

            reference.type = resource_type
            reference.identifier = cls.build_reference_identifier(obj, reference_type)
            reference.reference = f'{resource_type}/{resource_id}'

            if display:
                reference.display = display

            return reference

    @classmethod
    def get_resource_id_from_reference(cls, reference):
        _, resource_id, _ = cls._get_type_and_id_from_reference(reference)
        return resource_id

    @classmethod
    def get_resource_type_from_reference(cls, reference):
        path, _, _ = cls._get_type_and_id_from_reference(reference)
        return path


    @classmethod
    def get_database_query_id_parameteres_from_reference(cls, reference, code_keyword_name = 'code'):
        _, resource_id, id_type = cls._get_type_and_id_from_reference(reference)
        id_parameters = {}
        if cls._get_reference_type(id_type) == cls.CODE_REFERENCE_TYPE:
            id_parameters[code_keyword_name] = str(resource_id)
        else:
            try:
                id_parameters['uuid'] = uuid.UUID(resource_id)
            except:
                #fall back on code for unvalid uuid
                id_type=code_keyword_name
                id_parameters[code_keyword_name]=resource_id
        return id_parameters

    @classmethod
    def _get_reference_type(cls, reference_type):
        if reference_type is None or reference_type.coding is None or \
            reference_type.coding[0] is None or \
            reference_type.coding[0].code is None:
            return cls.UUID_REFERENCE_TYPE
        if reference_type.coding[0].code.lower() == 'code':
            return cls.CODE_REFERENCE_TYPE 
        return cls.UUID_REFERENCE_TYPE


    @classmethod
    def _get_type_and_id_from_reference(cls, reference: Reference) -> Tuple[str, str, str]:
        """
        Extracts resource type and resource id from FHIR reference.
        """
        resource_id, path, code_type = None, None, None
        if reference:
            
            if reference.reference and isinstance(reference.reference, str) and '/' in reference.reference:
                path, resource_id = reference.reference.rsplit('/', 1)
            elif isinstance(reference.type, str) and reference.identifier is not None \
                and isinstance(reference.identifier.value, str):
                path = reference.type
                resource_id = reference.identifier.value
                if reference.identifier.type is not None:
                    code_type = reference.identifier.type
        if path is None or resource_id is None:
            raise FHIRRequestProcessException(
                [F'Invalid format of reference `{reference}`. '
                 F'Should be string with format <ReferenceType>/<ReferenceId>']
            )
        return path, resource_id, code_type

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

        if len(identifiers) == 0:
            logger.error(
                f"Failed to build reference of type {reference_type} for resource of type {type(cls)}."
            )
        return identifiers[0]
