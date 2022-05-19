from policy.services import EligibilityRequest
from api_fhir_r4.configurations import GeneralConfiguration, R4CoverageEligibilityConfiguration as Config
from api_fhir_r4.converters import BaseFHIRConverter, PatientConverter, ReferenceConverterMixin
from fhir.resources.money import Money
from fhir.resources.reference import Reference
from fhir.resources.period import Period
from fhir.resources.coverageeligibilityresponse import CoverageEligibilityResponse as FHIRCoverageEligibilityResponse, \
    CoverageEligibilityResponseInsuranceItem, \
    CoverageEligibilityResponseInsurance, CoverageEligibilityResponseInsuranceItemBenefit
from api_fhir_r4.models import CoverageEligibilityRequestV2 as FHIRCoverageEligibilityRequest
from api_fhir_r4.utils import TimeUtils
from insuree.models import InsureePolicy
from product.models import Product
from policy.services import EligibilityResponse
from django.db import connection
from claim.models import Claim, ClaimService, ClaimItem
from medical.models import Item, Service


class CoverageEligibilityRequestConverter(BaseFHIRConverter):

    @classmethod
    def to_fhir_obj(cls, coverage_eligibility_response, coverage_eligibility_request, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_eligibility_response = {}
        fhir_eligibility_response["status"] = 'active'
        fhir_eligibility_response["outcome"] = 'complete'

        reference_insurer = {}
        reference_insurer["reference"] = 'openIMIS'
        fhir_eligibility_response["insurer"] = reference_insurer

        reference_patient = {}
        reference_patient["reference"] = f'Patient/{coverage_eligibility_request.chf_id}'
        fhir_eligibility_response['patient'] = reference_patient

        reference_coverage_eligibility_request = {}
        reference_coverage_eligibility_request["reference"] = f'CoverageEligibilityRequest'
        fhir_eligibility_response['request'] = reference_coverage_eligibility_request

        fhir_eligibility_response["purpose"] = ["benefits"]
        fhir_eligibility_response["created"] = TimeUtils.date().isoformat()
        fhir_response = FHIRCoverageEligibilityResponse(**fhir_eligibility_response)
        for item in coverage_eligibility_response.items:
            if item.status in Config.get_fhir_active_policy_status():
                cls.build_fhir_insurance(fhir_response, item, coverage_eligibility_request)
        return fhir_response

    @classmethod
    def to_imis_obj(cls, fhir_coverage_eligibility_request, audit_user_id):
        fhir_coverage_eligibility_request = FHIRCoverageEligibilityRequest(**fhir_coverage_eligibility_request)
        chf_id = cls.build_imis_chf(fhir_coverage_eligibility_request)
        item_code, service_code = cls.build_imis_item_service(fhir_coverage_eligibility_request)
        return EligibilityRequest(chf_id, service_code, item_code)

    @classmethod
    def build_fhir_insurance(cls, fhir_response, item, request):
        result = CoverageEligibilityResponseInsurance.construct()
        cls.build_fhir_coverage(result, item.policy_uuid)
        cls.build_fhir_benefit_period(result, item.start_date, item.expiry_date)
        # get the data from SP
        try:
            with connection.cursor() as cur:
                sql = """\
                            DECLARE @MinDateService DATE, @MinDateItem DATE,
                                    @ServiceLeft INT, @ItemLeft INT,
                                    @isItemOK BIT, @isServiceOK BIT;
                            EXEC [dbo].[uspServiceItemEnquiry] @CHFID = %s, @ServiceCode = %s, @ItemCode = %s,
                                 @MinDateService = @MinDateService OUTPUT, @MinDateItem = @MinDateItem OUTPUT,
                                 @ServiceLeft = @ServiceLeft OUTPUT, @ItemLeft = @ItemLeft OUTPUT,
                                 @isItemOK = @isItemOK OUTPUT, @isServiceOK = @isServiceOK OUTPUT;
                            SELECT @MinDateService, @MinDateItem, @ServiceLeft, @ItemLeft, @isItemOK, @isServiceOK
                        """
                cur.execute(sql, (request.chf_id,
                                  request.service_code,
                                  request.item_code))
                res = cur.fetchone()  # retrieve the stored proc @Result table
                if res is None:
                    response_eligibility_sp = EligibilityResponse(
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

                (prod_id, total_admissions_left, total_visits_left, total_consultations_left, total_surgeries_left,
                 total_deliveries_left, total_antenatal_left, consultation_amount_left, surgery_amount_left,
                 delivery_amount_left,
                 hospitalization_amount_left, antenatal_amount_left) = res
                cur.nextset()
                (min_date_service, min_date_item, service_left,
                 item_left, is_item_ok, is_service_ok) = cur.fetchone()
                response_eligibility_sp = EligibilityResponse(
                    eligibility_request=request,
                    prod_id=prod_id or None,
                    total_admissions_left=total_admissions_left or 0,
                    total_visits_left=total_visits_left or 0,
                    total_consultations_left=total_consultations_left or 0,
                    total_surgeries_left=total_surgeries_left or 0,
                    total_deliveries_left=total_deliveries_left or 0,
                    total_antenatal_left=total_antenatal_left or 0,
                    consultation_amount_left=consultation_amount_left or 0.0,
                    surgery_amount_left=surgery_amount_left or 0.0,
                    delivery_amount_left=delivery_amount_left or 0.0,
                    hospitalization_amount_left=hospitalization_amount_left or 0.0,
                    antenatal_amount_left=antenatal_amount_left or 0.0,
                    min_date_service=min_date_service,
                    min_date_item=min_date_item,
                    service_left=service_left or 0,
                    item_left=item_left or 0,
                    is_item_ok=is_item_ok is True,
                    is_service_ok=is_service_ok is True
                )
        except:
            response_eligibility_sp = EligibilityResponse(
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

        # build coverag item - product/benefit
        result.item = []
        cls.build_fhir_benefit_item_element(result, response_eligibility_sp)
        # check services and items etc
        service_claim = ClaimService.objects.filter(
            claim__insuree__chf_id=request.chf_id,
            validity_to=None).values('service').distinct()
        item_claim = ClaimItem.objects.filter(
            claim__insuree__chf_id=request.chf_id,
            validity_to=None).values('item').distinct()
        # build coverag item - service
        if service_claim.count() > 0:
            cls.build_fhir_benefit_item_service_element(result, response_eligibility_sp, service_claim)
        # build coverag item - item
        if item_claim.count() > 0:
            cls.build_fhir_benefit_item_item_element(result, response_eligibility_sp, item_claim)
        if type(fhir_response.insurance) is not list:
            fhir_response.insurance = [result]
        else:
            fhir_response.insurance.append(result)

    @classmethod
    def build_fhir_coverage(cls, insurance, policy_uuid):
        reference_coverage = Reference.construct()
        reference_coverage.reference = F"Coverage/{policy_uuid}"
        insurance.coverage = reference_coverage

    @classmethod
    def build_fhir_benefit_period(cls, insurance, start_date, expiry_date):
        benefit_period = Period.construct()
        benefit_period.start = start_date
        benefit_period.end = expiry_date
        insurance.benefitPeriod = benefit_period

    @classmethod
    def build_fhir_benefit_item_element(cls, insurance, response):
        item = CoverageEligibilityResponseInsuranceItem.construct()
        system = F"{GeneralConfiguration.get_system_base_url()}CodeSystem/coverage-item-category"
        item.category = cls.build_codeable_concept(
            system=system,
            code="benefit",
            display="Benefit Package"
        )
        cls.__build_item_product_name(fhir_item=item, prod_id=response.prod_id)
        item.benefit = []
        if response.total_admissions_left:
            cls.build_fhir_int_item_benefit_element(
                item=item,
                code="admissions_left",
                display="total_admissions",
                value=response.total_admissions_left
            )
        if response.total_consultations_left:
            cls.build_fhir_int_item_benefit_element(
                item=item,
                code="consultations_left",
                display="total_consultations",
                value=response.total_consultations_left
            )
        if response.total_surgeries_left:
            cls.build_fhir_int_item_benefit_element(
                item=item,
                code="surgeries_left",
                display="total_surgeries",
                value=response.total_surgeries_left
            )
        if response.total_deliveries_left:
            cls.build_fhir_int_item_benefit_element(
                item=item,
                code="deliveries_left",
                display="total_deliveries",
                value=response.total_deliveries_left
            )
        if response.total_visits_left:
            cls.build_fhir_int_item_benefit_element(
               item=item,
               code="visits_left",
               display="total_visits",
               value=response.total_visits_left
            )
        if response.total_antenatal_left:
            cls.build_fhir_int_item_benefit_element(
                item=item,
                code="antenatal_left",
                display="total_antenatal",
                value=response.total_antenatal_left
            )
        if response.hospitalization_amount_left:
            cls.build_fhir_money_item_benefit_element(
                item=item,
                code="hospitalization_amount",
                display="hospitalization_amount",
                value=response.hospitalization_amount_left
            )
        if response.delivery_amount_left:
            cls.build_fhir_money_item_benefit_element(
                item=item,
                code="delivery_amount",
                display="delivery_amount",
                value=response.delivery_amount_left
            )
        if response.surgery_amount_left:
            cls.build_fhir_money_item_benefit_element(
                item=item,
                code="surgery_amount",
                display="surgery_amount",
                value=response.surgery_amount_left
            )
        if response.consultation_amount_left:
            cls.build_fhir_money_item_benefit_element(
                item=item,
                code="consultation_amount",
                display="consultation_amount",
                value=response.consultation_amount_left
            )
        if response.antenatal_amount_left:
            cls.build_fhir_money_item_benefit_element(
                item=item,
                code="antenatal_amount",
                display="antenatal_amount",
                value=response.antenatal_amount_left
            )
        insurance.item.append(item)

    @classmethod
    def build_fhir_benefit_item_item_element(cls, insurance, response, item_claim):
        item = CoverageEligibilityResponseInsuranceItem.construct()
        system = F"{GeneralConfiguration.get_system_base_url()}CodeSystem/coverage-item-category"
        item.category = cls.build_codeable_concept(
            system=system,
            code="item",
            display="Item"
        )
        item.benefit = []
        if response.min_date_item:
            cls.build_fhir_string_item_benefit_element(
                item=item,
                code="min_date_item",
                display="Mininum date",
                value=response.min_date_item
            )
        if response.item_left:
            cls.build_fhir_int_item_benefit_element(
                item=item,
                code="item_left",
                display="Items left",
                value=response.service_left
            )
        code = Item.objects.get(id=item_claim.first()['item'], validity_to=None).code
        item.productOrService = cls.build_simple_codeable_concept(code)
        item.excluded = not response.is_service_ok
        insurance.item.append(item)

    @classmethod
    def build_fhir_benefit_item_service_element(cls, insurance, response, service_claim):
        item = CoverageEligibilityResponseInsuranceItem.construct()
        system = F"{GeneralConfiguration.get_system_base_url()}CodeSystem/coverage-item-category"
        item.category = cls.build_codeable_concept(
            system=system,
            code="service",
            display="Service"
        )
        item.benefit = []
        if response.min_date_service:
            cls.build_fhir_string_item_benefit_element(
                item=item,
                code="min_date_item",
                display="Mininum date",
                value=response.min_date_item
            )
        if response.item_left:
            cls.build_fhir_int_item_benefit_element(
                item=item,
                code="service_left",
                display="Services left",
                value=response.item_left
            )
        code = Service.objects.get(id=service_claim.first()['service'], validity_to=None).code
        item.productOrService = cls.build_simple_codeable_concept(code)
        item.excluded = not response.is_item_ok
        insurance.item.append(item)

    @classmethod
    def build_fhir_int_item_benefit_element(cls, item, code, display, value):
        system = F"{GeneralConfiguration.get_system_base_url()}CodeSystem/coverage-item-benefit-type"
        benefit = CoverageEligibilityResponseInsuranceItemBenefit.construct()
        benefit.type = cls.build_codeable_concept(
            system=system,
            code=code,
            display=display
        )
        benefit.allowedUnsignedInt = value
        item.benefit.append(benefit)

    @classmethod
    def build_fhir_money_item_benefit_element(cls, item, code, display, value):
        system = F"{GeneralConfiguration.get_system_base_url()}CodeSystem/coverage-item-benefit-type"
        benefit = CoverageEligibilityResponseInsuranceItemBenefit.construct()
        benefit.type = cls.build_codeable_concept(
            system=system,
            code=code,
            display=display
        )
        money_value = Money.construct()
        money_value.value = value
        benefit.allowedMoney = money_value
        item.benefit.append(benefit)

    @classmethod
    def build_fhir_string_item_benefit_element(cls, item, code, display, value):
        system = F"{GeneralConfiguration.get_system_base_url()}CodeSystem/coverage-item-benefit-type"
        benefit = CoverageEligibilityResponseInsuranceItemBenefit.construct()
        benefit.type = cls.build_codeable_concept(
            system=system,
            code=code,
            display=display
        )
        benefit.allowedString = value
        item.benefit.append(benefit)

    @classmethod
    def build_imis_chf(cls, fhir_coverage_eligibility_request):
        chf_id = None
        patient_reference = fhir_coverage_eligibility_request.patient
        if patient_reference:
            chf_id = PatientConverter.get_resource_id_from_reference(patient_reference)
        return chf_id

    @classmethod
    def build_imis_item_service(cls, fhir_coverage_eligibility_request):
        service_code = None
        item_code = None
        if fhir_coverage_eligibility_request.item:
            for item in fhir_coverage_eligibility_request.item:
                type_service = cls.__get_code_from_codeable_concept_by_coding_code(item.category)
                if type_service == 'item':
                    item_code = item.productOrService.text
                if type_service == 'service':
                    service_code = item.productOrService.text
        return item_code, service_code

    @classmethod
    def __get_code_from_codeable_concept_by_coding_code(cls, codeable_concept):
        service_code = None
        if codeable_concept:
            coding = cls.get_first_coding_from_codeable_concept(codeable_concept)
            if coding:
                service_code = coding.code
        return service_code

    @classmethod
    def __get_coverage_data(cls, response):
        policy = InsureePolicy.objects.filter(
            insuree__chf_id=response.eligibility_request.chf_id,
            validity_to__isnull=True).first().policy
        product = Product.objects.get(id=response.prod_id, validity_to__isnull=True)
        return policy, product

    @classmethod
    def __build_item_product_name(cls, fhir_item, prod_id):
        product_queryset = Product.objects.all().filter(id=prod_id, validity_to=None)
        product = product_queryset.first()
        fhir_item.name = product.name
        fhir_item.description = product.code
