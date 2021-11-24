from typing import List

from api_fhir_r4.converters.containedResourceConverter import ContainedResourceConverter
from fhir.resources.fhirabstractmodel import FHIRAbstractModel


class ContainedContentSerializerMixin:
    """
    Mixin for extending BaseFHIRSerializer. The creation of a FHIR representation through to_representation is extended
    with a "contained" value. It contains model attributes mapped to FHIR through ContainedResourceConverters
    listed contained_resources. The contained values are added only if the 'contained'
    value in the serializer context is set to True.
    """

    #  Used for determining what reference type will be used used in contained value,
    # if None then value from ContainedResourceConverter is used

    @property
    def contained_resources(self) -> List[ContainedResourceConverter]:
        """ List of ContainedResourceConverter objects, used to determine which attributes will be contained.
        :return:
        """
        raise NotImplementedError('Serializer with contained resources require contained_resources implemented')

    def fhir_object_reference_fields(self, fhir_obj: FHIRAbstractModel) -> List[FHIRAbstractModel]:
        """
        When contained resources are used, the references in fhir object fields should
        change to the contained resource reference starting with hash.
        References for values listed in this property will be changed.
        :return: List of fields from fhir_objects with references, which have representation in contained resources
        """
        raise NotImplementedError('fhir_object_reference_fields not implemented')

    def _get_converted_resources(self, obj):
        converted_values = []
        for resource in self.contained_resources:
            resource_fhir_repr = resource.convert_from_source(obj)
            converted_values.append((resource, resource_fhir_repr))
        return converted_values

    def to_representation(self, obj):
        base_fhir_obj_repr = super(ContainedContentSerializerMixin, self).to_representation(obj)
        if self.context.get('contained', False):
            base_fhir_obj_repr['contained'] = self._create_contained_obj_dict(obj)
        return base_fhir_obj_repr

    def _create_contained_obj_dict(self, obj):
        contained_resources = self.create_contained_resource_fhir_implementation(obj)
        dict_list = [resource.dict() for resource in contained_resources]
        for contained_resource in dict_list:
            contained_resource['id'] = F"{contained_resource['resourceType']}/{contained_resource['id']}"
        return dict_list

    def create_contained_resource_fhir_implementation(self, obj) -> List[FHIRAbstractModel]:
        contained_resources = []
        for resource, fhir_repr in self._get_converted_resources(obj):
            contained_resources.extend(fhir_repr)
        return contained_resources

    def _add_contained_references(self, fhir_obj: FHIRAbstractModel):
        for field in self.fhir_object_reference_fields(fhir_obj):
            field.reference = self._create_contained_reference(field.reference)

    def _create_contained_reference(self, base_reference):
        # Contained references are made by adding hash
        return F"#{base_reference}"
