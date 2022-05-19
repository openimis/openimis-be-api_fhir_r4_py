from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass

from typing import Type, Dict, Callable, Any

from django.db import models

from api_fhir_r4.containedResources.containedResourceHandler import ContainedResourceManager
from api_fhir_r4.containedResources.converters import FHIRContainedResourceConverter, IMISContainedResourceConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


@dataclass
class ContainedResourceDefinition:
    # Based on FHIRContainedResourceConverter definition
    imis_field: str = None
    fhir_field: str = None
    extraction_method: Callable[[models.Model, str], Any] = lambda model, attribute: model.__getattribute__(attribute)


class AbstractContainedResourceCollection(ABC):
    def __init__(self, *args, **kwargs):
        self._build_contained_resource_managers(*args, **kwargs)

    def get_contained(self) -> Dict[BaseFHIRSerializer, ContainedResourceManager]:
        return self.__contained

    def update_reference_type(self, reference_type):
        for contained in self.__contained.values():
            if contained.imis_converter:
                contained.imis_converter.reference_type = reference_type
            if contained.fhir_converter:
                contained.fhir_converter.reference_type = reference_type

    def _build_contained_resource_managers(self, *args, **kwargs):
        # sys.setrecursionlimit(10_000)
        self.__contained = {}
        for serializer, definition in self._definitions_for_serializers().items():
            args_copy, kwargs_copy = copy(args), copy(kwargs)
            serializer_instance = serializer(*args_copy, **kwargs_copy)
            contained_manager = self._build_resource_from_serializer(serializer_instance)
            self.__contained[serializer_instance] = contained_manager

    @classmethod
    @abstractmethod
    def _definitions_for_serializers(cls) -> Dict[Type[BaseFHIRSerializer], ContainedResourceDefinition]:
        """
        Binds contained resource definition to serializer.
        """
        pass

    @classmethod
    def _build_resource_from_serializer(cls, serializer: BaseFHIRSerializer) -> ContainedResourceManager:
        reference_type = serializer.reference_type
        converter = serializer.fhirConverter
        definition = cls._definitions_for_serializers()[type(serializer)]

        fhir_converter, imis_converter = None, None

        if definition.imis_field:
            fhir_converter = FHIRContainedResourceConverter(
                imis_resource_name=definition.imis_field,
                converter=converter,
                resource_extract_method=definition.extraction_method,
                reference_type=reference_type
            )

        if definition.fhir_field:
            imis_converter = IMISContainedResourceConverter(
                resource_reference_type=definition.fhir_field,
                converter=converter,
                reference_type=reference_type
            )

        return ContainedResourceManager(fhir_converter, imis_converter, serializer, cls._create_alias(definition))

    @classmethod
    def _create_alias(cls, contained_resource_definition):
        return F"{contained_resource_definition.imis_field}__{contained_resource_definition.fhir_field}"
