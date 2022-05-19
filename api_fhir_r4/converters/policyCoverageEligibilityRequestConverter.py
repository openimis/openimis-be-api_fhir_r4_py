# TODO uncomment if someone need this converter with connection to openHIM

"""
from policy.services import ByInsureeRequest

from api_fhir_r4.configurations import R4CoverageEligibilityConfiguration as Config
from api_fhir_r4.converters import BaseFHIRConverter, PatientConverter
from fhir.resources.money import Money
from fhir.resources.coverageeligibilityresponse import CoverageEligibilityResponse as FHIREligibilityResponse, \
    CoverageEligibilityResponseInsuranceItem, CoverageEligibilityResponseInsurance, CoverageEligibilityResponseInsuranceItemBenefit
from api_fhir_r4.models import CoverageEligibilityRequestV2 as FHIREligibilityRequest
from api_fhir_r4.utils import TimeUtils
"""
"""
class PolicyCoverageEligibilityRequestConverter(BaseFHIRConverter):

    @classmethod
    def to_fhir_obj(cls, eligibility_response):
        fhir_response = FHIREligibilityResponse.construct()
        try:
            for item in eligibility_response.items:
                if item.status in Config.get_fhir_active_policy_status():
                    cls.build_fhir_insurance(fhir_response, item)
        except:
            for item in eligibility_response['items']:
                if type(fhir_response.insurance) is not list:
                    fhir_response.insurance = [item]
                else:
                    fhir_response.insurance.append(item)
        return fhir_response

    @classmethod
    def to_imis_obj(cls, fhir_eligibility_request, audit_user_id):
        fhir_eligibility_request["status"] = "active"
        fhir_eligibility_request["purpose"] = ["validation"]
        fhir_eligibility_request["created"] = TimeUtils.date().isoformat()
        fhir_eligibility_request = FHIREligibilityRequest(**fhir_eligibility_request)
        uuid = cls.build_imis_uuid(fhir_eligibility_request)
        return ByInsureeRequest(uuid)

    @classmethod
    def build_fhir_insurance(cls, fhir_response, response):
        result = CoverageEligibilityResponseInsurance.construct()
        #cls.build_fhir_insurance_contract(result, response)
        cls.build_fhir_money_item(result, Config.get_fhir_balance_code(),
                                  response.ceiling,
                                  response.ded)
        if type(fhir_response.insurance) is not list:
            fhir_response.insurance = [result]
        else:
            fhir_response.insurance.append(result)

    '''
    @classmethod
    def build_fhir_insurance_contract(cls, insurance, contract):
        insurance.contract = ContractConverter.build_fhir_resource_reference(
            contract)
    '''

    @classmethod
    def build_fhir_money_item(cls, insurance, code, allowed_value, used_value):
        item = cls.build_fhir_generic_item(code)
        cls.build_fhir_money_item_benefit(
            item, allowed_value, used_value)
        if type(insurance.item) is not list:
            insurance.item = [item]
        else:
            insurance.item.append(item)

    @classmethod
    def build_fhir_generic_item(cls, code):
        item = CoverageEligibilityResponseInsuranceItem.construct()
        item.category = cls.build_simple_codeable_concept(
            Config.get_fhir_balance_default_category())
        return item

    @classmethod
    def build_fhir_money_item_benefit(cls, item, allowed_value, used_value):
        benefit = cls.build_fhir_generic_item_benefit()
        allowed_money_value = Money.construct()
        allowed_money_value.value = allowed_value or 0
        benefit.allowedMoney = allowed_money_value
        used_money_value = Money.construct()
        used_money_value.value = used_value or 0
        benefit.usedMoney = used_money_value
        if type(item.benefit) is not list:
            item.benefit = [benefit]
        else:
            item.benefit.append(benefit)

    @classmethod
    def build_fhir_generic_item_benefit(cls):
        benefit = CoverageEligibilityResponseInsuranceItemBenefit()
        benefit.type = cls.build_simple_codeable_concept(
            Config.get_fhir_financial_code())
        return benefit

    @classmethod
    def build_imis_uuid(cls, fhir_eligibility_request):
        uuid = None
        patient_reference = fhir_eligibility_request.patient
        if patient_reference:
            uuid = PatientConverter.get_resource_id_from_reference(
                patient_reference)
        return uuid
"""
