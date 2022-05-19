import logging
from policy.services import EligibilityRequest, EligibilityService, EligibilityResponse, StoredProcEligibilityService
from policy.services import ByInsureeRequest, ByInsureeService, ByInsureeResponse
from api_fhir_r4.converters import CoverageEligibilityRequestConverter
from api_fhir_r4.serializers import BaseFHIRSerializer
from django.http.response import HttpResponseBase
from fhir.resources.fhirabstractmodel import FHIRAbstractModel
from api_fhir_r4.converters import OperationOutcomeConverter


class CoverageEligibilityRequestSerializer(BaseFHIRSerializer):

    fhirConverter = CoverageEligibilityRequestConverter()
    logger = logging.getLogger(__name__)

    def to_representation(self, obj):
        if isinstance(obj, HttpResponseBase):
            return OperationOutcomeConverter.to_fhir_obj(obj).dict()
        elif isinstance(obj, FHIRAbstractModel):
            return obj.dict()
        return CoverageEligibilityRequestConverter.to_fhir_obj(obj[0], obj[1]).dict()

    def create(self, validated_data):
        eligibility_request_sp = EligibilityRequest(
            chf_id=validated_data.get('chf_id'),
            service_code=validated_data.get('service_code'),
            item_code=validated_data.get('item_code')
        )
        eligibility_request = ByInsureeRequest(chf_id=validated_data.get('chf_id'))
        request = self.context.get("request")
        try:
            response = ByInsureeService(request.user).request(eligibility_request)
        except TypeError:
            self.logger.warning('The insuree with chfid `{}` is not connected with policy. '
                                'The default eligibility response will be used.'
                                .format(validated_data.get('chfid')))
            response = self.create_default_eligibility_response()
        output_response = [response, eligibility_request_sp]
        return output_response

    def create_default_eligibility_response(self):
        return ByInsureeResponse(
            by_insuree_request=None,
            items=[]
        )
