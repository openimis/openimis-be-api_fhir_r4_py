import json
from fhir.resources.R4B.fhirtypes import ReferenceType
from typing import Iterable, List

from fhir.resources.R4B.reference import Reference

from api_fhir_r4.apps import logger
from api_fhir_r4.converters import BaseFHIRConverter
from api_fhir_r4.exceptions import FHIRRequestProcessException, FHIRException
from django.utils.translation import gettext as _


class ContainedResourceProcessException(FHIRRequestProcessException):
    pass


def get_converted_contained_resource(
        contained: Iterable,
        reference: ReferenceType,
        converter_for_contained: BaseFHIRConverter,
        audit_user_id: int
):
    def validate_contained_reference(ref):
        if isinstance(ref, str) and '/' in ref and ref[0] == '#':
            return True


    def _validate_matching_contained(matching: List):
        if len(matching) > 1:
            logger.warning([
                f'More than one contained resource definition found for reference '
                f'{reference}, references should be unique.']
            )
            logger.debug(f"Dupliacted contained resources: {matching}")

    if reference:
        reference = reference.reference
        if not validate_contained_reference(reference):
            return None
        path, resource_id = reference.split('/', maxsplit=1)
        resource_type = path[1:]
        contained = [
            n for n in contained if n.resource_type == resource_type and n.id == resource_id
        ]

        _validate_matching_contained(contained)
        if len(contained) > 0:
            return converter_for_contained.to_imis_obj(contained[0].__dict__, audit_user_id)

    return None


def get_from_contained_or_by_reference(fhir_reference, contained, converter, audit_user_id):
    """
    For given fhir reference, function checks if definition is provided in contained resource. If contained resource
    exists it's converted to IMIS type using converter and returned.
    If definition is not found in contained resource then internal value for reference is returned.

    @param fhir_reference: FHIR Reference to IMIS resource
    @param contained: Collection of contained resources
    @param converter: BaseFHIRConverter, has to implement get_imis_obj_by_fhir_reference and to_imis_obj
    @param audit_user_id: ID of user performing operation
    """

    value = None
    if fhir_reference:
        if contained:
            value = get_converted_contained_resource(contained, fhir_reference, converter, audit_user_id)
        value = value or converter.get_imis_obj_by_fhir_reference(fhir_reference)
        if value is None:
            raise FHIRException(
            "Failed to find the resource based on reference(with contain: {}, converter: {}): {}".format(
                (contained is not None), converter.__name__, str(fhir_reference))
            )
    return value
