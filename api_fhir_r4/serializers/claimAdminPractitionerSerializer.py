import copy
import uuid

from core.models.user import ClaimAdmin

from api_fhir_r4.converters import ClaimAdminPractitionerConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer


class ClaimAdminPractitionerSerializer(BaseFHIRSerializer):

    fhirConverter = ClaimAdminPractitionerConverter

    def create(self, validated_data):
        code = validated_data.get('code')
        if 'uuid' in validated_data.keys() and validated_data.get('uuid') is None:
            # In serializers using graphql services can't provide uuid. If uuid is provided then
            # resource is updated and not created. This check ensure UUID was provided.
            validated_data['uuid'] = uuid.uuid4()
        elif 'uuid' in validated_data and isinstance(validated_data['uuid'], str):
            validated_data['uuid'] = uuid.UUID(validated_data['uuid'])
        if ClaimAdmin.objects.filter(code=code).count() > 0:
            raise FHIRException('Exists practitioner with following code `{}`'.format(code))
        copied_data = copy.deepcopy(validated_data)
        if '_state' in copied_data:
            del copied_data['_state']
        return ClaimAdmin.objects.create(**copied_data)

    def update(self, instance, validated_data):
        if 'uuid' in validated_data and isinstance(validated_data['uuid'], str):
            validated_data['uuid'] = uuid.UUID(validated_data['uuid'])
        instance.code = validated_data.get('code', instance.code)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.other_names = validated_data.get('other_names', instance.other_names)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.email_id = validated_data.get('email_id', instance.email_id)
        instance.audit_user_id = self.get_audit_user_id()
        instance.save()
        return instance
