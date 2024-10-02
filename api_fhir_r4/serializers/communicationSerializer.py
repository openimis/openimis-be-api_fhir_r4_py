import copy
from api_fhir_r4.converters import CommunicationConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer
from claim.models import Claim, Feedback


class CommunicationSerializer(BaseFHIRSerializer):

    fhirConverter = CommunicationConverter

    def create(self, validated_data):
        claim = validated_data.get('claim_id')
        if Claim.objects.filter(id=claim, validity_to__isnull=True).count() == 0:
            raise FHIRException('Claim does not exist')
        if Feedback.objects.filter(claim__id=claim, validity_to__isnull=True).count() > 0:
            raise FHIRException('Feedback exists for this claim')
        copied_data = copy.deepcopy(validated_data)
        if '_state' in copied_data:
            del copied_data['_state']
        from core import datetime
        copied_data['feedback_date'] = datetime.datetime.now()
        obj = Feedback.objects.create(**copied_data)
        imis_claim = Claim.objects.get(id=claim)
        imis_claim.feedback_status = Claim.FEEDBACK_DELIVERED
        imis_claim.feedback_available = True
        imis_claim.feedback = obj
        imis_claim.save()
        return obj
