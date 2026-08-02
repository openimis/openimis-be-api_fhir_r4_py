import logging
from policy.services import ByPolicyRequest, ByPolicyResponse, ByPolicyService, EligibilityRequest, EligibilityService, EligibilityResponse
from api_fhir_r4.converters import CoverageEligibilityRequestConverter
from api_fhir_r4.serializers.baseSerializer import BaseFHIRSerializer
from django.http.response import HttpResponseBase
from fhir.resources.R4B import FHIRAbstractModel
from api_fhir_r4.converters import OperationOutcomeConverter


class CoverageEligibilityRequestSerializer(BaseFHIRSerializer):

    fhirConverter = CoverageEligibilityRequestConverter
    logger = logging.getLogger(__name__)

    def to_representation(self, obj):
        if isinstance(obj, HttpResponseBase):
            return OperationOutcomeConverter.to_fhir_obj(obj).dict()
        elif isinstance(obj, FHIRAbstractModel):
            return obj.dict()
        return CoverageEligibilityRequestConverter.to_fhir_obj(obj[0], obj[1]).dict()

    def create(self, validated_data):
        request = self.context.get("request")
        eligibility_request_sp = EligibilityRequest(
            validated_data.get("chf_id"),
            validated_data.get("service_code"),
            validated_data.get("item_code"),
            validated_data.get("policy_uuid")
        )
        try:
            response = EligibilityService(request.user).request(eligibility_request_sp)
        except TypeError:
            self.logger.warning(
                "The insuree with chfid `{}` is not connected with policy. "
                "The default eligibility response will be used.".format(
                    validated_data.get("chf_id")
                )
            )
            response = self.create_default_eligibility_response(eligibility_request_sp)
        output_response = [response, eligibility_request_sp]
        return output_response

    def create_default_eligibility_response(self, request):
        return EligibilityResponse(eligibility_request=request)
