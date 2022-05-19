import logging
from abc import ABC, abstractmethod
from typing import List, Callable, Iterable, Union

from django.core.exceptions import MultipleObjectsReturned
from django.db import models, IntegrityError
from django.forms import model_to_dict

from api_fhir_r4.containedResources.converters import FHIRContainedResourceConverter, IMISContainedResourceConverter
from fhir.resources.fhirabstractmodel import FHIRAbstractModel

from api_fhir_r4.serializers import BaseFHIRSerializer
from location.models import HealthFacility


logger = logging.getLogger(__name__)


class ContainedResourceManager:
    """It's used for managing contained resources in fhir objects

    Methods
    ----------
    convert_to_fhir(imis_obj: models.Model):
        Convert IMIS Model attribute to FHIR Object

    convert_to_imis(imis_obj: models.Model):
        Convert FHIR Object contained resource to IMIS Model

    create_or_update_from_contained(self, fhir_model: dict) -> List[models.Model]
        Takes contained resources from fhir dict representation and saves them in database. If resource
        for given resource ID already exists then it updates object definition.
    """

    def __init__(
            self, fhir_converter: FHIRContainedResourceConverter = None,
            imis_converter: IMISContainedResourceConverter = None,
            serializer: BaseFHIRSerializer = None,
            alias: str = None
    ):
        self.fhir_converter = fhir_converter
        self.imis_converter = imis_converter
        self.serialzier = serializer
        self.alias = alias

    def convert_to_fhir(self, imis_obj: models.Model) -> List[FHIRAbstractModel]:
        self._assert_fhir_converter()
        return self.fhir_converter.convert(imis_obj)

    def convert_to_imis(self, fhir_model: dict) -> List[models.Model]:
        self._assert_imis_converter()
        return self.imis_converter.convert(fhir_model, self.serialzier.get_audit_user_id())

    def create_or_update_from_contained(self, fhir_model: dict) -> List[models.Model]:
        self._assert_serializer()
        imis_representation = self.convert_to_imis(fhir_model)
        output = []
        for instance in imis_representation:
            if instance.uuid and self._is_saved_in_db(instance):
                output.append(self._update(instance))
            else:
                output.append(self._create(instance))

        return output

    def _assert_fhir_converter(self):
        assert self.fhir_converter is not None, "FHIR Converter is required"

    def _assert_imis_converter(self):
        assert self.imis_converter is not None, "IMIS Converter is required"

    def _assert_serializer(self):
        assert self.serialzier is not None, "Serializer is required to perform create and update"

    def _update(self, updated_instance):
        try:
            instance = updated_instance.__class__.objects.get(uuid=updated_instance.uuid)
        except MultipleObjectsReturned as a:
            logger.error(a)
            raise IntegrityError(
                F"While trying to use resource {updated_instance} for update of object"
                F" with uuid {updated_instance.uuid} multiple objects with this uuid were found") from a

        try:
            updated = self.serialzier.update(instance, self._model_to_dict(updated_instance))
            updated.save()
            return updated
        except Exception as e:
            import warnings
            warnings.warn(
                F"Update from contained resource failed due to error: \n{e}.\n"
                F"Instance will not be updated and default value will be used")
            return instance

    def _create(self, instance):
        # Services from other modules are often called through update_or_create method. It treats objects with uuid
        # as updatable. If non-existing object with explicitly given uuid is about to be created it'll try to update
        # it instead. Therefore, uuid is temporary removed and overwritten after object is created.
        as_dict = self._model_to_dict(instance)
        uuid = as_dict.get('uuid', None)
        as_dict['uuid'] = None
        created = self.serialzier.create(as_dict)
        if uuid:
            created.uuid = uuid
            created.save()
        return created

    def _is_saved_in_db(self, obj: models.Model):
        # Checks if given ID is already stored in database
        return obj.__class__.objects.filter(uuid=obj.uuid).exists()

    def _model_to_dict(self, instance):
        # Due to how serializers are build simple __dict__ is used instead of builtin model_to_dict
        return instance.__dict__
