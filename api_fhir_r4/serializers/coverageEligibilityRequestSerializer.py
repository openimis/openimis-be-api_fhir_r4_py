import logging

from policy.services import EligibilityRequest, EligibilityService, EligibilityResponse

from api_fhir_r4.converters import CoverageEligibilityRequestConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


class CoverageEligibilityRequestSerializer(BaseFHIRSerializer):

    fhirConverter = CoverageEligibilityRequestConverter()
    logger = logging.getLogger(__name__)

    def create(self, validated_data):
        eligibility_request = EligibilityRequest(chf_id=validated_data.get('chf_id'),
                                                 service_code=validated_data.get('service_code'),
                                                 item_code=validated_data.get('item_code'))
        request = self.context.get("request")
        try:
            response = EligibilityService(request.user).request(eligibility_request)
        except TypeError:
            self.logger.warning('The insuree with chfid `{}` is not connected with policy. '
                                'The default eligibility response will be used.'
                                .format(validated_data.get('chfid')))
            response = self.create_default_eligibility_response()
        return response

    def create_default_eligibility_response(self):
        return EligibilityResponse(
            eligibility_request=None,
            prod_id=None,
            total_admissions_left=0,
            total_visits_left=0,
            total_consultations_left=0,
            total_surgeries_left=0,
            total_deliveries_left=0,
            total_antenatal_left=0,
            consultation_amount_left=0.0,
            surgery_amount_left=0.0,
            delivery_amount_left=0.0,
            hospitalization_amount_left=0.0,
            antenatal_amount_left=0.0,
            min_date_service=None,
            min_date_item=None,
            service_left=0,
            item_left=0,
            is_item_ok=False,
            is_service_ok=False
        )
