import copy

from insuree.models import Family, Insuree
from api_fhir_r4.converters import GroupConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer
from insuree.services import FamilyService, InsureeService
from core.models import resolve_id_reference

from django.forms.models import model_to_dict

class GroupSerializer(BaseFHIRSerializer):
    fhirConverter = GroupConverter()

    def create(self, validated_data):
        #validated_data = resolve_id_reference(Family, validated_data)
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
        new_family = FamilyService(user).create_or_update(copied_data)

        # assign members of family (insuree) to the family
        for mf in members_family:
            mf = mf.__dict__
            del mf['_state']
            mf['family_id'] = new_family.id
            InsureeService(user).create_or_update(mf)

        return new_family

    def update(self, instance, validated_data):
        #validated_data = resolve_id_reference(validated_data)
        # TODO: This doesn't work
        request = self.context.get("request")
        validated_data.pop('_state')
        members_family = validated_data.pop('members_family')
        user = request.user
        head_id = validated_data.get('head_insuree_id', None)
        family_uuid = validated_data.get('uuid', None)
        if head_id:
            family = Family.objects.filter(head_insuree_id=head_id, validity_to__isnull=True).first()
            if not family:
                raise FHIRException('No family with following head id `{}`'.format(head_id))
        elif family_uuid:
            family = Family.objects.filter(uuid=family_uuid, validity_to__isnull=True).first()
            if not family:
                raise FHIRException('No family with following uuid `{}`'.format(head_id))
            
        validated_data["id"] = family.id
        validated_data["uuid"] = family.uuid
        instance = FamilyService(user).create_or_update(validated_data)
        for mf in members_family:
            mf = mf.__dict__
            mf.pop('_state')
            mf['family_id'] = instance.id
            InsureeService(user).create_or_update(mf)
            
        
        
        
        return instance
