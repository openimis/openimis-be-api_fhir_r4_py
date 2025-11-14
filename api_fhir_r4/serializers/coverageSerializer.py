from api_fhir_r4.converters.coverageConverter import CoverageConverter
from api_fhir_r4.serializers.baseSerializer import BaseFHIRSerializer
from policy.models import Policy
import copy
from api_fhir_r4.exceptions import FHIRException


class CoverageSerializer(BaseFHIRSerializer):
    fhirConverter = CoverageConverter

    def create(self, validated_data):
        family = validated_data.get("family_id")
        if Policy.objects.filter(family_id=family).count() > 0:
            raise FHIRException("Exists coverage with the family  provided")
        copied_data = copy.deepcopy(validated_data)
        if "_state" in copied_data:
            del copied_data["_state"]
        return Policy.objects.create(**copied_data)

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        instance.value = validated_data.get("value", instance.value)
        instance.save()
        return instance
