from typing import List, Type, Dict

from fhir.resources.R4B import FHIRAbstractModel

from api_fhir_r4.containedResources.containedResourceHandler import ContainedResourceManager
from api_fhir_r4.containedResources.containedResources import AbstractContainedResourceCollection
from api_fhir_r4.serializers import BaseFHIRSerializer


class ContainedContentSerializerMixin:
    """
    Mixin for extending BaseFHIRSerializer. The creation of a FHIR representation through to_representation is extended
    with a "contained" value. It contains model attributes mapped to FHIR through ContainedResourceConverters
    listed contained_resources. The contained values are added only if the 'contained'
    value in the serializer context is set to True.
    """
    ALLOWED_RESOURCE_UPDATE_CONTAINED = {
        'Group':('Patient'), 
        'Patient':('Group'),
        'Claim':('Medication','ActivityDefinition','Organization','Patient','Practitioner','PractitionerRole','Group'),
        }

    #  Used for determining what reference type will be used used in contained value,
    # if None then value from ContainedResourceManager is used

    def __init__(self, *args, **kwargs):
        self.__contained_definitions = None
        # Serializers for contained resources are created with same argument as main serializer
        self.build_contained_resource_managers(*args, **kwargs)
        super().__init__(*args, **kwargs)

    @property
    def _contained_definitions(self) -> AbstractContainedResourceCollection:
        return self.__contained_definitions

    def build_contained_resource_managers(self, *args, **kwargs):
        self.__contained_definitions = self.contained_resources(*args, **kwargs)

    @property
    def contained_resources(self) -> Type[AbstractContainedResourceCollection]:
        """ Collection definition, used to determine which managers will be used for defining contained resources.
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
        for resource in self._contained_definitions.get_contained().values():
            resource_fhir_repr = resource.convert_to_fhir(obj)
            converted_values.append((resource, resource_fhir_repr))
        return converted_values

    def to_internal_value(self, data):
        audit_user_id = self.get_audit_user_id()
        imis_obj = self.fhirConverter(user=self.user).to_imis_obj(data, audit_user_id)
        # Filter out special attributes
        return {k: v for k, v in imis_obj.__dict__.items() if not k.startswith('_') and v is not None}

    def create(self, validated_data):
        self._create_or_update_contained(validated_data)
        super(ContainedContentSerializerMixin, self).create(validated_data)

    def update(self, instance, validated_data):
        self._create_or_update_contained(validated_data)
        super(ContainedContentSerializerMixin, self).update(instance, validated_data)

    def to_representation(self, obj):
        base_fhir_obj_repr = super(ContainedContentSerializerMixin, self).to_representation(obj)
        if self.context.get('contained', False):
            base_fhir_obj_repr['contained'] = self._create_contained_obj_dict(obj)
        return base_fhir_obj_repr

    def _create_contained_obj_dict(self, obj):
        contained_resources = self.create_contained_resource_fhir_implementation(obj)
        dict_list = [resource.dict() for resource in contained_resources]
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

    def _create_or_update_contained(self, validated_data):
        result = {}
        main_resource_type = validated_data['resourceType']
        #TODO: use a bundle instead 
        if 'contained' in validated_data\
            and main_resource_type in self.ALLOWED_RESOURCE_UPDATE_CONTAINED:
            for resource in self._contained_definitions.get_contained().values():
                name = resource.alias
                ressource_type = resource.imis_converter.fhir_resource_type
                for contained in validated_data['contained']:
                    if 'resourceType' in contained and contained['resourceType'] == ressource_type\
                        and contained['resourceType'] in self.ALLOWED_RESOURCE_UPDATE_CONTAINED[main_resource_type]:
                        result[name] = resource.create_or_update_from_contained(contained)
                        break
        return result
