import copy

from insuree.models import Family
from api_fhir_r4.converters import GroupConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer


class GroupSerializer(BaseFHIRSerializer):
    fhirConverter = GroupConverter()

    def create(self, validated_data):
        chf_id = validated_data.get('head_insuree_id')
        if Family.objects.filter(head_insuree_id=chf_id).count() > 0:
            raise FHIRException('Exists family with the provided head')
        copied_data = copy.deepcopy(validated_data)
        del copied_data['_state']
        return Family.objects.create(**copied_data)

    def update(self, instance, validated_data):
        return instance
