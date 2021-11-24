import copy
from medical.models import Diagnosis
from api_fhir_r4.converters import ConditionConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer


class ConditionSerializer(BaseFHIRSerializer):
    fhirConverter = ConditionConverter

    def create(self, validated_data):
        code = validated_data.get('code')
        if Diagnosis.objects.filter(code=code).count() > 0:
            raise FHIRException('Exists condition with following code `{}`'.format(code))
        copied_data = copy.deepcopy(validated_data)
        del copied_data['_state']
        return Diagnosis.objects.create(**copied_data)

    def update(self, instance, validated_data):
        instance.code = validated_data.get('code', instance.code)
        instance.id = validated_data.get('id', instance.id)
        instance.name = validated_data.get('name', instance.name)
        instance.validity_from = validated_data.get('package', instance.validity_from)
        return instance
