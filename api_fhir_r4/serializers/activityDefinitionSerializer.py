import copy
import uuid
import warnings

from medical.models import Service
from api_fhir_r4.converters import ActivityDefinitionConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


class ActivityDefinitionSerializer(BaseFHIRSerializer):
    fhirConverter = ActivityDefinitionConverter

    def create(self, validated_data):
        if 'uuid' in validated_data.keys() and validated_data.get('uuid') is None:
            # In serializers using graphql services can't provide uuid. If uuid is provided then
            # resource is updated and not created. This check ensure UUID was provided.
            validated_data['uuid'] = uuid.uuid4()
        elif isinstance(validated_data['uuid'], str):
            validated_data['uuid'] = uuid.UUID(validated_data['uuid'])
            
        copied_data = copy.deepcopy(validated_data)
        if '_state' in copied_data:
            del copied_data['_state']
        return Service.objects.create(**copied_data)

    def update(self, instance, validated_data):
        instance.code = validated_data.get('code', instance.code)
        instance.name = validated_data.get('name', instance.name)
        instance.validity_from = validated_data.get('validity_from', instance.validity_from)
        instance.patient_category = validated_data.get('patient_category', instance.patient_category)
        instance.category = validated_data.get('category', instance.category)
        instance.care_type = validated_data.get('care_type', instance.care_type)
        instance.type = validated_data.get('type', instance.type)
        instance.price = validated_data.get('price', instance.price)
        instance.save()
        return instance
