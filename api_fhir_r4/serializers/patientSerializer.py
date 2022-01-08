import copy

from insuree.apps import InsureeConfig
from insuree.models import Insuree, Gender, Education, Profession, Family, InsureePhoto
from insuree.gql_mutations import update_or_create_insuree, create_file

from api_fhir_r4.converters import PatientConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer


class PatientSerializer(BaseFHIRSerializer):
    fhirConverter = PatientConverter()

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        chf_id = validated_data.get('chf_id')
        if Insuree.objects.filter(chf_id=chf_id).count() > 0:
            raise FHIRException('Exists patient with following chfid `{}`'.format(chf_id))
        copied_data = copy.deepcopy(validated_data)
        if '_state' in validated_data:
            del copied_data['_state']
        obj = update_or_create_insuree(copied_data, user)
        # create photo as a file to specified configured path
        if InsureeConfig.insuree_photos_root_path:
            create_file(date=obj.photo.date, insuree_id=obj.id, photo_bin=obj.photo.photo)
        if copied_data['head']:
            obj.family = Family.objects.create(head_insuree=obj, audit_user_id=copied_data['audit_user_id'])
            obj.save()
        return obj

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user
        chf_id = validated_data.get('chf_id')
        if Insuree.objects.filter(chf_id=chf_id).count() == 0:
            raise FHIRException('No patients with following chfid `{}`'.format(chf_id))
        insuree = Insuree.objects.get(chf_id=chf_id, validity_to__isnull=True)
        validated_data["id"] = insuree.id
        validated_data["uuid"] = insuree.uuid
        del validated_data['_state']
        instance = update_or_create_insuree(validated_data, user)
        return instance
