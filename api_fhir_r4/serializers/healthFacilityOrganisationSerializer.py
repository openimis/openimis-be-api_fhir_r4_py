import copy

from location.gql_mutations import update_or_create_health_facility

from api_fhir_r4.converters import HealthFacilityOrganisationConverter
from api_fhir_r4.serializers import BaseFHIRSerializer

import uuid
class HealthFacilityOrganisationSerializer(BaseFHIRSerializer):
    fhirConverter = HealthFacilityOrganisationConverter

    def create(self, validated_data):
        data = copy.deepcopy(validated_data)
        if 'uuid' in validated_data and isinstance(validated_data['uuid'], str):
            validated_data['uuid'] = uuid.UUID(validated_data['uuid'])
        # UUID is automatically generated for HF model, has to be removed as create_or_update will fail.
        return self.__create_or_update(data)

    def update(self, instance, validated_data):
        validated_data['id'] = instance.id
        validated_data['uuid'] = instance.uuid

        data = copy.deepcopy(validated_data)
        return self.__create_or_update(data)

    def __create_or_update(self, validated_data):
        request = self.context.get("request")
        user = request.user
        data = copy.deepcopy(validated_data)
        if '_state' in validated_data:
            del data['_state']

        if not data.get('offline', None):
            data['offline'] = False

        return update_or_create_health_facility(data, user)
