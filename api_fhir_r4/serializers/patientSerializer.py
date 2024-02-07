import copy

from insuree.apps import InsureeConfig
from insuree.models import Insuree, Family

from core.models import resolve_id_reference

from api_fhir_r4.converters import PatientConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer
from insuree.services import InsureeService


class PatientSerializer(BaseFHIRSerializer):
    fhirConverter = PatientConverter()

    def create(self, validated_data):
        #validated_data = resolve_id_reference(Insuree, validated_data)
        self._validate_data(validated_data.get('chf_id'))
        copied_data = self._clean_data(copy.deepcopy(validated_data))
        obj = InsureeService(self.context.get("request").user)\
            .create_or_update(copied_data)

        if copied_data['head']:
            self._create_patient_family(obj, validated_data)
        return obj

    def update(self, instance, validated_data):
        #validated_data = resolve_id_reference(Insuree, validated_data)
        request = self.context.get("request")
        validated_data.pop('_state')
        user = request.user
        chf_id = validated_data.get('chf_id', None)
        if Insuree.objects.filter(chf_id=chf_id).count() == 0:
            raise FHIRException('No patients with following chfid `{}`'.format(chf_id))
        insuree = Insuree.objects.get(chf_id=chf_id, validity_to__isnull=True)
        validated_data["id"] = insuree.id
        validated_data["uuid"] = insuree.uuid
        instance = InsureeService(user).create_or_update(validated_data)
        return instance

    def _validate_data(self, chf_id):
        if not chf_id:
            raise FHIRException("Provided patient without code.")

        if Insuree.objects.filter(chf_id=chf_id, validity_to__isnull=True).exists():
            raise FHIRException('Exists patient with following chfid `{}`'.format(chf_id))

    def _clean_data(self, validated_data):
        validated_data.pop('_state', None)
        validated_data.pop('family_address', None)
        validated_data.pop('family_location', None)
        return validated_data

    def _create_patient_family(self, obj, validated_data):
        audit_user_id = validated_data['audit_user_id']
        family_location = validated_data.get('family_location', None)
        family_address = validated_data.get('family_address', None)

        obj.family = Family.objects.create(
            location=family_location,
            address=family_address,
            head_insuree=obj,
            audit_user_id=audit_user_id
        )
        obj.save()
