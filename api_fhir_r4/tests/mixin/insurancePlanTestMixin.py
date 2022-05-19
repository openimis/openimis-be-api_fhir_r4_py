import core
import decimal

from product.models import Product

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import InsurancePlanConverter
from api_fhir_r4.tests import GenericTestMixin

from django.utils.translation import gettext as _
from fhir.resources.extension import Extension
from fhir.resources.money import Money
from fhir.resources.insuranceplan import InsurancePlan, InsurancePlanCoverage, \
    InsurancePlanCoverageBenefit, InsurancePlanCoverageBenefitLimit, \
    InsurancePlanPlan, InsurancePlanPlanGeneralCost
from fhir.resources.period import Period
from fhir.resources.identifier import Identifier
from fhir.resources.quantity import Quantity
from api_fhir_r4.utils import TimeUtils


class InsurancePlanTestMixin(GenericTestMixin):

    _TEST_PRODUCT_CODE = "TEST0001"
    _TEST_PRODUCT_NAME = "Test Product"
    _TEST_PERIOD_START = "2017-01-01T00:00:00"
    _TEST_PERIOD_END = "2030-12-31T00:00:00"
    _TEST_MAX_INSTALLMENTS = 3
    _TEST_GRACE_PERIOD_PAYMENT = 1
    _TEST_INSURANCE_PERIOD = 12
    _TEST_MEMBER_COUNT = 9999
    _TEST_LUMPSUM = 0
    _TEST_THRESHOLD = 6
    _TEST_PREMIUM_ADULT = 4000
    _TEST_RENEWAL_DISCOUNT = 40
    _TEST_RENEWAL_DISCOUNT_PERIOD = 1
    _TEST_ENROLMENT_DISCOUNT = 30
    _TEST_ENROLMENT_DISCOUNT_PERIOD = 1

    def create_test_imis_instance(self):
        imis_product = Product()
        imis_product.code = self._TEST_PRODUCT_CODE
        imis_product.name = self._TEST_PRODUCT_NAME
        imis_product.date_from = TimeUtils.str_to_date(self._TEST_PERIOD_START)
        imis_product.date_to = TimeUtils.str_to_date(self._TEST_PERIOD_END)
        imis_product.max_installments = self._TEST_MAX_INSTALLMENTS
        imis_product.grace_period_enrolment = self._TEST_GRACE_PERIOD_PAYMENT
        imis_product.insurance_period = self._TEST_INSURANCE_PERIOD
        imis_product.max_members = self._TEST_MEMBER_COUNT
        imis_product.lump_sum = self._TEST_LUMPSUM
        imis_product.threshold = self._TEST_THRESHOLD
        imis_product.premium_adult = self._TEST_PREMIUM_ADULT
        imis_product.renewal_discount_perc = self._TEST_RENEWAL_DISCOUNT
        imis_product.renewal_discount_period = self._TEST_RENEWAL_DISCOUNT_PERIOD
        imis_product.enrolment_discount_perc = self._TEST_ENROLMENT_DISCOUNT
        imis_product.enrolment_discount_period = self._TEST_ENROLMENT_DISCOUNT_PERIOD
        return imis_product

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_PRODUCT_CODE, imis_obj.code)
        self.assertEqual(self._TEST_PRODUCT_NAME, imis_obj.name)
        self.assertEqual(self._TEST_PERIOD_START, imis_obj.date_from.isoformat())
        self.assertEqual(self._TEST_PERIOD_END, imis_obj.date_to.isoformat())
        self.assertEqual(self._TEST_MAX_INSTALLMENTS, imis_obj.max_installments)
        self.assertEqual(self._TEST_GRACE_PERIOD_PAYMENT, imis_obj.grace_period_enrolment)
        self.assertEqual(self._TEST_INSURANCE_PERIOD, imis_obj.insurance_period)
        self.assertEqual(self._TEST_MEMBER_COUNT, imis_obj.max_members)
        self.assertEqual(self._TEST_LUMPSUM, imis_obj.lump_sum)
        self.assertEqual(self._TEST_THRESHOLD, imis_obj.threshold)
        self.assertEqual(self._TEST_PREMIUM_ADULT, imis_obj.premium_adult)

    def create_test_fhir_instance(self):
        if hasattr(core, 'currency'):
            currency = core.currency
        else:
            currency = "EUR"

        fhir_insurance_plan = InsurancePlan.construct()

        code = InsurancePlanConverter.build_fhir_identifier(
            self._TEST_PRODUCT_CODE,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        identifiers = [code]
        fhir_insurance_plan.identifier = identifiers
        fhir_insurance_plan.name = self._TEST_PRODUCT_NAME

        type = InsurancePlanConverter.build_codeable_concept(
            code="medical",
            system="http://terminology.hl7.org/CodeSystem/insurance-plan-type"
        )
        if len(type.coding) == 1:
            type.coding[0].display = _("Medical")
        fhir_insurance_plan.type = [type]

        period = Period.construct()
        period.start = self._TEST_PERIOD_START
        period.end = self._TEST_PERIOD_END
        fhir_insurance_plan.period = period

        coverage = InsurancePlanCoverage.construct()
        coverage.type = InsurancePlanConverter.build_codeable_concept(
            code="medical",
            system="http://terminology.hl7.org/CodeSystem/insurance-plan-type"
        )

        # build coverage benefit
        benefit = InsurancePlanCoverageBenefit.construct()
        benefit.type = InsurancePlanConverter.build_codeable_concept(
            code="medical",
            system="http://terminology.hl7.org/CodeSystem/insurance-plan-type"
        )

        # build coverage benefit limit slices
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/insurance-plan-coverage-benefit-limit"
        limit = InsurancePlanCoverageBenefitLimit.construct()
        quantity = Quantity.construct()
        quantity.value = self._TEST_INSURANCE_PERIOD
        quantity.unit = "month"
        limit.value = quantity
        limit.code = InsurancePlanConverter.build_codeable_concept("period", system)
        limit.code.coding[0].display = _("Period")
        benefit.limit = [limit]

        limit = InsurancePlanCoverageBenefitLimit.construct()
        quantity = Quantity.construct()
        quantity.value = self._TEST_MEMBER_COUNT
        quantity.unit = "member"
        limit.value = quantity
        limit.code = InsurancePlanConverter.build_codeable_concept("memberCount", system)
        limit.code.coding[0].display = _("Member Count")
        benefit.limit.append(limit)

        coverage.benefit = [benefit]
        fhir_insurance_plan.coverage = [coverage]

        plan = InsurancePlanPlan.construct()
        # build plan general cost limit slices
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/insurance-plan-general-cost-type"
        general_cost = InsurancePlanPlanGeneralCost.construct()
        cost = Money.construct()
        cost.value = self._TEST_LUMPSUM
        cost.currency = currency
        general_cost.cost = cost
        general_cost.type = InsurancePlanConverter.build_codeable_concept("lumpsum", system)
        general_cost.type.coding[0].display = _("Lumpsum")
        plan.generalCost = [general_cost]
        plan.generalCost[0].groupSize = self._TEST_THRESHOLD

        general_cost = InsurancePlanPlanGeneralCost.construct()
        cost = Money.construct()
        cost.value = self._TEST_PREMIUM_ADULT
        cost.currency = currency
        general_cost.cost = cost
        general_cost.type = InsurancePlanConverter.build_codeable_concept("premiumAdult", system)
        general_cost.type.coding[0].display = _("Premium Adult")
        plan.generalCost.append(general_cost)

        fhir_insurance_plan.plan = [plan]

        # extensions
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/insurance-plan-max-installments"
        extension.valueUnsignedInt = self._TEST_MAX_INSTALLMENTS
        fhir_insurance_plan.extension = [extension]
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/insurance-plan-period"
        extension.valueQuantity = Quantity(
            **{
                "value": self._TEST_GRACE_PERIOD_PAYMENT,
                "unit": "months"
            }
        )
        fhir_insurance_plan.extension.append(extension)

        # discount processing - renewal
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/insurance-plan-discount"
        nested_extension = Extension.construct()

        # percentage
        nested_extension.url = "Percentage"
        nested_extension.valueDecimal = self._TEST_RENEWAL_DISCOUNT
        extension.extension = [nested_extension]

        # period
        nested_extension = Extension.construct()
        nested_extension.url = "Period"
        nested_extension.valueQuantity = Quantity(
            **{
                "value": self._TEST_RENEWAL_DISCOUNT_PERIOD,
                "unit": "months"
            }
        )
        extension.extension.append(nested_extension)
        fhir_insurance_plan.extension.append(extension)

        # discount processing - enrolment
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/insurance-plan-discount"
        nested_extension = Extension.construct()

        # percentage
        nested_extension.url = "Percentage"
        nested_extension.valueDecimal = self._TEST_ENROLMENT_DISCOUNT
        extension.extension = [nested_extension]

        # period
        nested_extension = Extension.construct()
        nested_extension.url = "Period"
        nested_extension.valueQuantity = Quantity(
            **{
                "value": self._TEST_ENROLMENT_DISCOUNT_PERIOD,
                "unit": "months"
            }
        )
        extension.extension.append(nested_extension)
        fhir_insurance_plan.extension.append(extension)

        return fhir_insurance_plan

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual(4, len(fhir_obj.extension))
        extension_max_installment = fhir_obj.extension[0]
        self.assertTrue(isinstance(extension_max_installment, Extension))
        self.assertEqual(self._TEST_MAX_INSTALLMENTS, extension_max_installment.valueUnsignedInt)
        extension_grace_period = fhir_obj.extension[1].valueQuantity
        self.assertTrue(isinstance(extension_grace_period, Quantity))
        self.assertEqual(self._TEST_GRACE_PERIOD_PAYMENT, extension_grace_period.value)
        extension_renewal_discounts = fhir_obj.extension[2].extension
        self.assertAlmostEqual(decimal.Decimal(self._TEST_RENEWAL_DISCOUNT),
                               extension_renewal_discounts[0].valueDecimal, places=2)
        self.assertEqual(self._TEST_RENEWAL_DISCOUNT_PERIOD, extension_renewal_discounts[1].valueQuantity.value)
        extension_enrolment_discounts = fhir_obj.extension[3].extension
        self.assertAlmostEqual(decimal.Decimal(self._TEST_ENROLMENT_DISCOUNT),
                               extension_enrolment_discounts[0].valueDecimal, places=2)
        self.assertEqual(self._TEST_ENROLMENT_DISCOUNT_PERIOD, extension_enrolment_discounts[1].valueQuantity.value)
        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = InsurancePlanConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_claim_admin_code_type():
                self.assertEqual(self._TEST_PRODUCT_CODE, identifier.value)
        benefit_limit_period = fhir_obj.coverage[0].benefit[0].limit[0].value
        self.assertEqual(self._TEST_INSURANCE_PERIOD, benefit_limit_period.value)
        benefit_limit_member_count = fhir_obj.coverage[0].benefit[0].limit[1].value
        self.assertEqual(self._TEST_MEMBER_COUNT, benefit_limit_member_count.value)
        lumpsum = fhir_obj.plan[0].generalCost[0].cost.value
        self.assertEqual(self._TEST_LUMPSUM, lumpsum)
        threshold = fhir_obj.plan[0].generalCost[0].groupSize
        self.assertEqual(self._TEST_THRESHOLD, threshold)
        premium_adult = fhir_obj.plan[0].generalCost[1].cost.value
        self.assertEqual(self._TEST_PREMIUM_ADULT, premium_adult)
