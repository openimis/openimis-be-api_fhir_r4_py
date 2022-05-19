import copy

from insuree.models import Family, Insuree
from api_fhir_r4.converters import GroupConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer
from insuree.services import FamilyService, InsureeService


class GroupSerializer(BaseFHIRSerializer):
    fhirConverter = GroupConverter()

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        insuree_id = validated_data.get('head_insuree_id')
        members_family = validated_data.pop('members_family')

        if Family.objects.filter(head_insuree_id=insuree_id).count() > 0:
            raise FHIRException('Exists family with the provided head')

        insuree = Insuree.objects.get(id=insuree_id)
        copied_data = copy.deepcopy(validated_data)
        copied_data["head_insuree"] = insuree.__dict__
        copied_data["contribution"] = None
        del copied_data['_state']

        new_family = FamilyService(user).create_or_update(copied_data)

        # assign members of family (insuree) to the family
        for mf in members_family:
            mf = mf.__dict__
            del mf['_state']
            mf['family_id'] = new_family.id
            InsureeService(user).create_or_update(mf)

        return new_family

    def update(self, instance, validated_data):
        # TODO: This doesn't work
        request = self.context.get("request")
        user = request.user
        chf_id = validated_data.get('chf_id')
        if Family.objects.filter(head_insuree_id=chf_id).count() == 0:
            raise FHIRException('No family with following chfid `{}`'.format(chf_id))
        family = Family.objects.get(head_insuree_id=chf_id, validity_to__isnull=True)
        validated_data["id"] = family.id
        validated_data["uuid"] = family.uuid
        del validated_data['_state']
        instance = FamilyService(user).create_or_update(validated_data)
        return instance
