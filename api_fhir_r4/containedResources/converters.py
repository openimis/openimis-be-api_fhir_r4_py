import logging
from abc import ABC, abstractmethod
from typing import List, Callable, Iterable, Union
from django.db import models

from fhir.resources.R4B.resource import Resource

from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.exceptions import FHIRException
from fhir.resources.R4B import FHIRAbstractModel


DEFAULT_REF_TYPE = ReferenceConverterMixin.UUID_REFERENCE_TYPE
logger = logging.getLogger(__name__)


class _ConverterWrapper:

    def __init__(self, converter: BaseFHIRConverter):
        self.converter = converter

    def to_imis(self, resource: Union[Iterable[Resource], Resource], reference_type, audit_user):
        return self.__convert_to_imis(self.converter.to_imis_obj, resource, reference_type, [audit_user])

    def to_fhir(self, resource, reference_type):
        return self.__convert_to_fhir(self.converter.to_fhir_obj, resource, [reference_type])

    def __convert_to_fhir(self, method, resource, args):
        if not resource:
            return []

        try:
            if isinstance(resource, Iterable) and   'resourceType' not in resource:
                return [method(next_resource, *args) for next_resource in resource]
            else:
                return [method(resource, *args)]
        except BaseException as e:
            logger.error(f"Failed to process resource ({resource.__class__}/{resource.id if hasattr(resource, 'id') else '' }, "
                         f"reason: {e}")
            self.__raise_default_exception(resource, e)

    def __convert_to_imis(self, method, resource, reference_type, args):
        try:
            if isinstance(resource, Iterable) and 'resourceType' not in resource :
                return [
                    self.__convert_single_resource(next_, method, args, reference_type) for next_ in resource
                ]
            else:
                return [self.__convert_single_resource(resource, method, args, reference_type)]
        except BaseException as e:
            logger.error(f"Failed to process resource ({resource.get('resourceType')}/{resource.get('id')}, "
                         f"reason: {e}")
            self.__raise_default_exception(resource, e)

    def __convert_single_resource(self, resource, method, args, ref_type):
        converted = method(resource, *args)
        self.__bind_uuid_to_converted_resource(converted, resource, ref_type)
        return converted

    def __bind_uuid_to_converted_resource(self, converted, contained_fhir_resource: dict, reference_type):
        """
        By default, converters doesn't bind uuid to created resource. In that if id is explicitly given in contained
        resource this information will be lost in the process. Identifiers assigned from contained resource definitions
        are necessary for using contained resource in process of creating object from them. This is only available for
        UUID type identifiers.
        """
        assert reference_type == DEFAULT_REF_TYPE, \
            f'Invalid reference type, assigning contained resource uuid explicitly is available only for ' \
            f'{DEFAULT_REF_TYPE}'

        assert contained_fhir_resource.get('id') is not None, \
            F'Resources created from contained data requires non empty ID field.'
        converted.uuid = contained_fhir_resource['id']

    def __raise_default_exception(self, resource, error):
        raise FHIRException(
            "Failed to process resource: {}, using converter {}. Error: {}".format(
                resource, self.converter, str(error)
            )
        )


class FHIRContainedResourceConverter:
    def __init__(self, imis_resource_name, converter, resource_extract_method=None, reference_type=DEFAULT_REF_TYPE):
        """
        Parameters
        ----------
        :param imis_resource_name: Name of attribute, which value should be transformed.
        :param converter: FHIR Converter, it's used for mapping imis resource to fhir representation.
        It must implement at least to_fhir_obj() method.
        :param resource_extract_method: Optional argument. Function used for getting attribute value from IMIS Model.
        It has two arguments, first is django model, second one is imis_resource_name. Default function is
        imis_model.__getattribute__(imis_resource_name). Return type can be model or iterable (e.g. list of attributes).
        :param reference_type: Optional argument. Determine what object value will be used as reference and id.
        """
        self.imis_resource_name = imis_resource_name
        self.extract_value = resource_extract_method or (lambda model, attribute: model.__getattribute__(attribute))
        self.converter = _ConverterWrapper(converter)
        self.reference_type = reference_type

    def convert(self, imis_obj: models.Model) -> List[FHIRAbstractModel]:
        """Convert IMIS Model attribute to FHIR Object.

        :param imis_obj: IMIS Object with attribute that have to be converted.
        :return: Attribute converted to FHIR object list. If attribute is single object then it's still converted to
        list format.
        """
        resource = self.extract_value(imis_obj, self.imis_resource_name)
        return self.converter.to_fhir(resource, self.reference_type)


class IMISContainedResourceConverter:
    def __init__(self, resource_reference_type, converter, reference_type=DEFAULT_REF_TYPE):
        """
        Parameters
        ----------
        :param resource_reference_type: Contained resource type
        :param converter: FHIR Converter, it's used for mapping fhir resource to imis representation.
        It must implement at least to_imis_obj() method.
        :param resource_extract_method: Optional argument. Function used for getting attribute value from IMIS Model.
        It has two arguments, first is django model, second one is imis_resource_name. Default function is
        imis_model.__getattribute__(imis_resource_name). Return type can be model or iterable (e.g. list of attributes).
        :param reference_type: Optional argument. Determine what object value will be used as reference and id.
        """
        self.fhir_resource_type = resource_reference_type
        self.converter = _ConverterWrapper(converter)
        self.reference_type = reference_type

    def convert(self, fhir_dict_repr: dict, audit_user_id: int = None) -> List[models.Model]:
        """Extracts FHIR contained resource based on resource_type and converts to IMIS object.

        :param fhir_dict_repr: FHIR Dict representation with contained key that have to be converted.
        :param audit_user_id: Id of user performing given operation.
        :return: Attribute converted to FHIR object list. If attribute is single object then it's still converted to
        list format.
        """
        resource = None
        if fhir_dict_repr:
            if 'resourceType' in fhir_dict_repr and fhir_dict_repr['resourceType'] == self.fhir_resource_type:
                resource = fhir_dict_repr
            else:
                resource = [r for r in fhir_dict_repr.get('contained', {}) if r['resourceType'] == self.fhir_resource_type]
            if resource:
                return self.converter.to_imis(resource, self.reference_type, audit_user_id)
        
        return None