# TODO uncomment if someone need this serializer with connection to openHIM

"""
import logging
import os
import requests
from rest_framework.response import Response
from requests.auth import HTTPBasicAuth
from rest_framework import status
from policy.services import ByInsureeRequest, ByInsureeService, ByInsureeResponse
from api_fhir_r4.converters import PolicyCoverageEligibilityRequestConverter
from api_fhir_r4.serializers import BaseFHIRSerializer
"""

"""
class PolicyCoverageEligibilityRequestSerializer(BaseFHIRSerializer):

    fhirConverter = PolicyCoverageEligibilityRequestConverter()
    logger = logging.getLogger(__name__)
    def create(self, validated_data):
        data = self.context.get("request").data
        data['resourceType'] = "CoverageEligibilityRequest"
        url=os.environ.get('OPEHNHIM_URL')
        technical_user =os.environ.get('OPEHNHIM_USER')
        password = os.environ.get('OPEHNHIM_PASSWORD')
        try:
            response = requests.post(url+'CoverageEligibilityRequest',json=data,auth=HTTPBasicAuth(technical_user,password))
            if response.status_code == 200 and len(response.json())>1:
                res = response.json()
                return {"items":res['insurance']['item']}
            else:
                return self.eligibility_check(validated_data.get('chf_id'))
        except:
            return self.eligibility_check(validated_data.get('chf_id'))
        
    def eligibility_check(self,data):
        eligibility_request = ByInsureeRequest(chf_id=data)
        request = self.context.get("request")
        try:
            response = ByInsureeService(request.user).request(eligibility_request)            
        except TypeError:
            self.logger.warning('The insuree with chfid `{}` is not connected with policy. '
                                'The default eligibility response will be used.'
                                .format(validated_data.get('chfid')))
            response = self.create_default_eligibility_response()
        return response

    def create_default_eligibility_response(self):
        return ByInsureeResponse(
            by_insuree_request=None,
            items=[]
        )
    
    def create_eligibility_response(self, by_insuree_request,items):
        return ByInsureeResponse(
            by_insuree_request= by_insuree_request,
            items= items
        )
"""
