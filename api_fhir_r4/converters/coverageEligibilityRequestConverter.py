from policy.services import EligibilityRequest
from api_fhir_r4.configurations import R4CoverageEligibilityConfiguration as Config
from api_fhir_r4.converters import BaseFHIRConverter, PatientConverter
from fhir.resources.money import Money
from fhir.resources.coverageeligibilityresponse import CoverageEligibilityResponse as FHIRCoverageEligibilityResponse, \
    CoverageEligibilityResponseInsuranceItem, CoverageEligibilityResponseInsurance, CoverageEligibilityResponseInsuranceItemBenefit
from api_fhir_r4.models import CoverageEligibilityRequestV2 as FHIRCoverageEligibilityRequest
from api_fhir_r4.utils import TimeUtils


class CoverageEligibilityRequestConverter(BaseFHIRConverter):

    @classmethod
    def to_fhir_obj(cls, coverage_eligibility_response):
        fhir_response = FHIRCoverageEligibilityResponse.construct()
        cls.build_fhir_insurance(fhir_response, coverage_eligibility_response)
        return fhir_response

    @classmethod
    def to_imis_obj(cls, fhir_coverage_eligibility_request, audit_user_id):
        fhir_coverage_eligibility_request["status"] = "active"
        fhir_coverage_eligibility_request["purpose"] = ["validation"]
        fhir_coverage_eligibility_request["created"] = TimeUtils.date().isoformat()
        fhir_coverage_eligibility_request = FHIRCoverageEligibilityRequest(**fhir_coverage_eligibility_request)
        chf_id = cls.build_imis_uuid(fhir_coverage_eligibility_request)
        service_code = cls.build_imis_service_code(fhir_coverage_eligibility_request)
        item_code = cls.build_imis_item_code(fhir_coverage_eligibility_request)
        return EligibilityRequest(chf_id, service_code, item_code)

    @classmethod
    def build_fhir_insurance(cls, fhir_response, response):
        result = CoverageEligibilityResponseInsurance.construct()
        cls.build_fhir_int_item(result, Config.get_fhir_total_admissions_code(), response.total_admissions_left)
        cls.build_fhir_int_item(result, Config.get_fhir_total_visits_code(), response.total_visits_left)
        cls.build_fhir_int_item(result, Config.get_fhir_total_consultations_code(),
                                   response.total_consultations_left)
        cls.build_fhir_int_item(result, Config.get_fhir_total_surgeries_code(), response.total_surgeries_left)
        cls.build_fhir_int_item(result, Config.get_fhir_total_deliveries_code(), response.total_deliveries_left)
        cls.build_fhir_int_item(result, Config.get_fhir_total_antenatal_code(), response.total_antenatal_left)
        cls.build_fhir_money_item(result, Config.get_fhir_consultation_amount_code(),
                                     response.consultation_amount_left)
        cls.build_fhir_money_item(result, Config.get_fhir_surgery_amount_code(), response.surgery_amount_left)
        cls.build_fhir_money_item(result, Config.get_fhir_delivery_amount_code(), response.delivery_amount_left)
        cls.build_fhir_money_item(result, Config.get_fhir_hospitalization_amount_code(),
                                     response.hospitalization_amount_left)
        cls.build_fhir_money_item(result, Config.get_fhir_antenatal_amount_code(), response.antenatal_amount_left)
        cls.build_fhir_int_item(result, Config.get_fhir_service_left_code(), response.service_left)
        cls.build_fhir_int_item(result, Config.get_fhir_item_left_code(), response.item_left)
        cls.build_fhir_bool_item(result, Config.get_fhir_is_service_ok_code(), response.is_service_ok)
        cls.build_fhir_bool_item(result, Config.get_fhir_is_item_ok_code(), response.is_item_ok)
        if type(fhir_response.insurance) is not list:
            fhir_response.insurance = [result]
        else:
            fhir_response.insurance.append(result)

    @classmethod
    def build_fhir_bool_item(cls, insurance, code, is_ok):
        if is_ok is not None:
            item = cls.build_fhir_generic_item(code)
            item.excluded = not is_ok
            if type(insurance.item) is not list:
                insurance.item = [item]
            else:
                insurance.item.append(item)

    @classmethod
    def build_fhir_int_item(cls, insurance, code, value):
        if value is not None:
            item = cls.build_fhir_generic_item(code)
            cls.build_fhir_int_item_benefit(item, value)
            if type(insurance.item) is not list:
                insurance.item = [item]
            else:
                insurance.item.append(item)

    @classmethod
    def build_fhir_money_item(cls, insurance, code, value):
        if value is not None:
            item = cls.build_fhir_generic_item(code)
            cls.build_fhir_money_item_benefit(item, value)
            if type(insurance.item) is not list:
                insurance.item = [item]
            else:
                insurance.item.append(item)

    @classmethod
    def build_fhir_generic_item(cls, code):
        item = CoverageEligibilityResponseInsuranceItem.construct()
        item.category = cls.build_simple_codeable_concept(code)
        return item

    @classmethod
    def build_fhir_int_item_benefit(cls, item, value):
        benefit = cls.build_fhir_generic_item_benefit()
        benefit.allowedUnsignedInt = value
        if type(item.benefit) is not list:
            item.benefit = [benefit]
        else:
            item.benefit.append(benefit)

    @classmethod
    def build_fhir_money_item_benefit(cls, item, value):
        benefit = cls.build_fhir_generic_item_benefit()
        money_value = Money.construct()
        money_value.value = value
        benefit.allowedMoney = money_value
        if type(item.benefit) is not list:
            item.benefit = [benefit]
        else:
            item.benefit.append(benefit)

    @classmethod
    def build_fhir_generic_item_benefit(cls):
        benefit = CoverageEligibilityResponseInsuranceItemBenefit.construct()
        benefit.type = cls.build_simple_codeable_concept(Config.get_fhir_financial_code())
        return benefit

    @classmethod
    def build_imis_uuid(cls, fhir_coverage_eligibility_request):
        uuid = None
        patient_reference = fhir_coverage_eligibility_request.patient
        if patient_reference:
            uuid = PatientConverter.get_resource_id_from_reference(patient_reference)
        return uuid

    @classmethod
    def build_imis_service_code(cls, fhir_coverage_eligibility_request):
        return cls.get_text_from_codeable_concept_by_coding_code(fhir_coverage_eligibility_request.item[0].category,
                                                                 Config.get_fhir_service_code())

    @classmethod
    def build_imis_item_code(cls, fhir_coverage_eligibility_request):
        return cls.get_text_from_codeable_concept_by_coding_code(fhir_coverage_eligibility_request.item[0].productOrService,
                                                                 Config.get_fhir_item_code())

    @classmethod
    def get_text_from_codeable_concept_by_coding_code(cls, codeable_concept, coding_code):
        service_code = None
        if codeable_concept:
            coding = cls.get_first_coding_from_codeable_concept(codeable_concept)
            if coding and coding.code == coding_code:
                service_code = codeable_concept.text
        return service_code
