import core

from django.utils.translation import gettext as _
from location.models import Location
from product.models import Product
from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.converters.locationConverter import LocationConverter
from fhir.resources.extension import Extension
from fhir.resources.money import Money
from fhir.resources.insuranceplan import InsurancePlan, InsurancePlanCoverage, \
    InsurancePlanCoverageBenefit, InsurancePlanCoverageBenefitLimit, \
    InsurancePlanPlan, InsurancePlanPlanGeneralCost
from fhir.resources.period import Period
from fhir.resources.reference import Reference
from fhir.resources.quantity import Quantity
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.utils import DbManagerUtils, TimeUtils


class InsurancePlanConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_product, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_insurance_plan = InsurancePlan.construct()
        # then create fhir object as usual
        cls.build_fhir_identifiers(fhir_insurance_plan, imis_product)
        cls.build_fhir_pk(fhir_insurance_plan, imis_product.uuid)
        cls.build_fhir_name(fhir_insurance_plan, imis_product)
        cls.build_fhir_type(fhir_insurance_plan, imis_product)
        cls.build_fhir_status(fhir_insurance_plan, imis_product)
        cls.build_fhir_period(fhir_insurance_plan, imis_product)
        cls.build_fhir_coverage_area(fhir_insurance_plan, imis_product)
        cls.build_fhir_coverage(fhir_insurance_plan, imis_product)
        cls.build_fhir_plan(fhir_insurance_plan, imis_product)
        cls.build_fhir_extentions(fhir_insurance_plan, imis_product)
        return fhir_insurance_plan

    @classmethod
    def to_imis_obj(cls, fhir_insurance_plan, audit_user_id):
        errors = []
        fhir_insurance_plan = InsurancePlan(**fhir_insurance_plan)
        imis_product = Product()
        imis_product.audit_user_id = audit_user_id
        cls.build_imis_name(imis_product, fhir_insurance_plan)
        cls.build_imis_identifiers(imis_product, fhir_insurance_plan)
        cls.build_imis_period(imis_product, fhir_insurance_plan)
        cls.build_imis_coverage_area(imis_product, fhir_insurance_plan)
        cls.build_imis_coverage(imis_product, fhir_insurance_plan)
        cls.build_imis_plan(imis_product, fhir_insurance_plan)
        cls.build_imis_extentions(imis_product, fhir_insurance_plan)
        cls.check_errors(errors)
        return imis_product

    @classmethod
    def get_reference_obj_id(cls, imis_product):
        return imis_product.uuid

    @classmethod
    def get_fhir_resource_type(cls):
        return InsurancePlan

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_insurance_uuid = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Product, uuid=imis_insurance_uuid)

    @classmethod
    def build_fhir_identifiers(cls, fhir_insurance_plan, imis_product):
        identifiers = []
        cls.build_fhir_uuid_identifier(identifiers, imis_product)
        cls.build_fhir_code_identifier(identifiers, imis_product)
        fhir_insurance_plan.identifier = identifiers

    @classmethod
    def build_imis_identifiers(cls, imis_product, fhir_insurance_plan):
        value = cls.get_fhir_identifier_by_code(fhir_insurance_plan.identifier,
                                                R4IdentifierConfig.get_fhir_generic_type_code())
        cls._validate_fhir_insurance_plan_identifier_code(value)
        imis_product.code = value

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

    @classmethod
    def build_fhir_name(cls, fhir_insurance_plan, imis_product):
        if imis_product.name and imis_product.name != "":
            fhir_insurance_plan.name = imis_product.name

    @classmethod
    def build_imis_name(cls, imis_product, fhir_insurance_plan):
        if fhir_insurance_plan.name and fhir_insurance_plan.name != "":
            imis_product.name = fhir_insurance_plan.name

    @classmethod
    def build_fhir_type(cls, fhir_insurance_plan, imis_product):
        fhir_insurance_plan.type = [cls.__build_insurance_plan_type()]

    @classmethod
    def __build_insurance_plan_type(cls):
        type = cls.build_codeable_concept(
            code="medical",
            system="http://terminology.hl7.org/CodeSystem/insurance-plan-type"
        )
        if len(type.coding) == 1:
            type.coding[0].display = _("Medical")
        return type

    @classmethod
    def build_fhir_status(cls, fhir_insurance_plan, imis_product):
        from core import datetime
        now = datetime.datetime.now()
        status = "unknown"
        if now < imis_product.date_from:
            status = "draft"
        elif now >= imis_product.date_from and now <= imis_product.date_to:
            status = "active"
        elif now > imis_product.date_to:
            status = "retired"
        fhir_insurance_plan.status = status

    @classmethod
    def build_fhir_period(cls, fhir_insurance_plan, imis_product):
        from core import datetime
        period = Period.construct()
        if imis_product.date_from:
            # check if datetime object
            if isinstance(imis_product.date_from, datetime.datetime):
                period.start = str(imis_product.date_from.date().isoformat())
            else:
                period.start = str(imis_product.date_from.isoformat())
        if imis_product.date_to:
            # check if datetime object
            if isinstance(imis_product.date_to, datetime.datetime):
                period.end = str(imis_product.date_to.date().isoformat())
            else:
                period.end = str(imis_product.date_to.isoformat())
        if period.start or period.end:
            fhir_insurance_plan.period = period

    @classmethod
    def build_imis_period(cls, imis_product, fhir_insurance_plan):
        if fhir_insurance_plan.period:
            period = fhir_insurance_plan.period
            if period.start:
                imis_product.date_from = TimeUtils.str_to_date(period.start)
            if period.end:
                imis_product.date_to = TimeUtils.str_to_date(period.end)

    @classmethod
    def build_fhir_coverage_area(cls, fhir_insurance_plan, imis_product):
        if imis_product.location:
            fhir_insurance_plan.coverageArea = [LocationConverter.build_fhir_resource_reference(imis_product.location, 'Location')]

    @classmethod
    def build_imis_coverage_area(cls, imis_product, fhir_insurance_plan):
        if fhir_insurance_plan.coverageArea:
            coverage_area = fhir_insurance_plan.coverageArea[0]
            value = cls.__get_location_reference(coverage_area.reference)
            if value:
                imis_product.location = Location.objects.get(uuid=value)

    @classmethod
    def __get_location_reference(cls, location):
        return location.rsplit('/', 1)[1]

    @classmethod
    def build_fhir_coverage(cls, fhir_insurance_plan, imis_product):
        # build coverage
        coverage = InsurancePlanCoverage.construct()
        coverage.type = cls.build_codeable_concept(
            code="medical",
            system="http://terminology.hl7.org/CodeSystem/insurance-plan-type"
        )

        # build coverage benefit
        benefit = InsurancePlanCoverageBenefit.construct()
        benefit.type = cls.build_codeable_concept(
            code="medical",
            system="http://terminology.hl7.org/CodeSystem/insurance-plan-type"
        )
        # build coverage benefit limit slices
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/insurance-plan-coverage-benefit-limit"
        benefit.limit = [
            cls.__build_fhir_limit(
                code="period",
                display=_("Period"),
                system=system,
                unit="month",
                value=imis_product.insurance_period
            )
        ]
        benefit.limit.append(
            cls.__build_fhir_limit(
                code="memberCount",
                display=_("Member Count"),
                system=system,
                unit="member",
                value=imis_product.max_members
            )
        )

        coverage.benefit = [benefit]
        fhir_insurance_plan.coverage = [coverage]

    @classmethod
    def build_imis_coverage(cls, imis_product, fhir_insurance_plan):
        if fhir_insurance_plan.coverage:
            if len(fhir_insurance_plan.coverage) == 1:
                benefit = fhir_insurance_plan.coverage[0].benefit
                cls.__build_imis_limit(imis_product, benefit[0].limit)

    @classmethod
    def __build_fhir_limit(cls, code, display, system, unit, value):
        limit = InsurancePlanCoverageBenefitLimit.construct()
        quantity = Quantity.construct()
        quantity.value = value
        quantity.unit = unit
        limit.value = quantity
        limit.code = cls.build_codeable_concept(code, system)
        limit.code.coding[0].display = _(display)
        return limit

    @classmethod
    def __build_imis_limit(cls, imis_product, benefit_limits):
        for limit in benefit_limits:
            if limit.code.coding[0].code == 'memberCount':
                imis_product.max_members = int(limit.value.value)
            if limit.code.coding[0].code == 'period':
                imis_product.insurance_period = int(limit.value.value)

    @classmethod
    def build_fhir_plan(cls, fhir_insurance_plan, imis_product):
        # get the currency defined in configs from core module
        if hasattr(core, 'currency'):
            currency = core.currency
        else:
            currency = "EUR"

        plan = InsurancePlanPlan.construct()
        # build plan general cost limit slices
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/insurance-plan-general-cost-type"
        plan.generalCost = [
            cls.__build_fhir_general_cost(
                code="lumpsum",
                display=_("Lumpsum"),
                system=system,
                currency=currency,
                value=imis_product.lump_sum
            )
        ]
        if imis_product.threshold:
            plan.generalCost[0].groupSize = imis_product.threshold

        if imis_product.premium_adult:
            plan.generalCost.append(
                cls.__build_fhir_general_cost(
                    code="premiumAdult",
                    display=_("Premium Adult"),
                    system=system,
                    currency=currency,
                    value=imis_product.premium_adult
                )
           )

        if imis_product.premium_child:
            plan.generalCost.append(
                cls.__build_fhir_general_cost(
                    code="premiumChild",
                    display=_("Premium Child"),
                    system=system,
                    currency=currency,
                    value=imis_product.premium_child
                )
           )

        if imis_product.registration_lump_sum:
            plan.generalCost.append(
                cls.__build_fhir_general_cost(
                    code="registrationLumpsum",
                    display=_("Registration Lumpsum"),
                    system=system,
                    currency=currency,
                    value=imis_product.registration_lump_sum
                )
           )

        if imis_product.registration_fee:
            plan.generalCost.append(
                cls.__build_fhir_general_cost(
                    code="registrationFee",
                    display=_("Registration Fee"),
                    system=system,
                    currency=currency,
                    value=imis_product.registration_fee
                )
           )

        if imis_product.general_assembly_lump_sum:
            plan.generalCost.append(
                cls.__build_fhir_general_cost(
                    code="generalAssemblyLumpSum",
                    display=_("General Assembly Lumpsum"),
                    system=system,
                    currency=currency,
                    value=imis_product.general_assembly_lump_sum
                )
           )

        if imis_product.general_assembly_fee:
            plan.generalCost.append(
                cls.__build_fhir_general_cost(
                    code="generalAssemblyFee",
                    display=_("General Assembly Fee"),
                    system=system,
                    currency=currency,
                    value=imis_product.general_assembly_fee
                )
           )

        fhir_insurance_plan.plan = [plan]

    @classmethod
    def build_imis_plan(cls, imis_product, fhir_insurance_plan):
        if fhir_insurance_plan.plan:
            if len(fhir_insurance_plan.plan) == 1:
                general_costs = fhir_insurance_plan.plan[0].generalCost
                cls.__build_imis_cost_values(imis_product, general_costs)

    @classmethod
    def __build_fhir_general_cost(cls, code, display, system, currency, value):
        general_cost = InsurancePlanPlanGeneralCost.construct()
        cost = Money.construct()
        cost.value = value
        cost.currency = currency
        general_cost.cost = cost
        general_cost.type = cls.build_codeable_concept(code, system)
        general_cost.type.coding[0].display = _(display)
        return general_cost

    @classmethod
    def __build_imis_cost_values(cls, imis_product, general_costs):
        for cost in general_costs:
            if cost.type.coding[0].code == 'lumpsum':
                imis_product.lump_sum = cost.cost.value
                if cost.groupSize:
                    imis_product.threshold = cost.groupSize
            if cost.type.coding[0].code == 'premiumAdult':
                imis_product.premium_adult = cost.cost.value
            if cost.type.coding[0].code == 'premiumChild':
                imis_product.premium_child = cost.cost.value
            if cost.type.coding[0].code == 'registrationLumpsum':
                imis_product.registration_lump_sum = cost.cost.value
            if cost.type.coding[0].code == 'registrationFee':
                imis_product.registration_fee = cost.cost.value
            if cost.type.coding[0].code == 'generalAssemblyLumpSum':
                imis_product.general_assembly_lump_sum = cost.cost.value
            if cost.type.coding[0].code == 'generalAssemblyFee':
                imis_product.general_assembly_fee = cost.cost.value

    @classmethod
    def get_reference_obj_uuid(cls, imis_product: Product):
        return imis_product.uuid

    @classmethod
    def build_fhir_extentions(cls, fhir_insurance_plan, imis_product):
        fhir_insurance_plan.extension = []

        def build_extension(fhir_insurance_plan, imis_product, value):
            extension = Extension.construct()
            if value == "conversion":
                extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/insurance-plan-{value}"

                reference_conversion = Reference.construct()
                reference_conversion.reference = F"InsurancePlan/{imis_product.code}"
                extension.valueReference = cls.build_fhir_resource_reference(imis_product, 'InsurancePlan')
                extension.valueReference.display = imis_product.code
            elif value == "max-installments":
                extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/insurance-plan-{value}"
                extension.valueUnsignedInt = imis_product.max_installments
            elif value == "start_cycle1":
                cls.__build_fhir_cycle(extension, value, imis_product.start_cycle_1)
            elif value == "start_cycle2":
                cls.__build_fhir_cycle(extension, value, imis_product.start_cycle_2)
            elif value == "start_cycle3":
                cls.__build_fhir_cycle(extension, value, imis_product.start_cycle_3)
            elif value == "start_cycle4":
                cls.__build_fhir_cycle(extension, value, imis_product.start_cycle_4)
            elif value == "administration-period":
                cls.__build_fhir_period_extension(extension, value, imis_product.administration_period)
            elif value == "payment-grace-period":
                cls.__build_fhir_period_extension(extension, value, imis_product.grace_period_enrolment)
            elif value == "renewal-grace-period":
                cls.__build_fhir_period_extension(extension, value, imis_product.grace_period_renewal)
            elif value == "renewal-discount":
                cls.__build_fhir_discount_extension(
                    extension=extension,
                    type_extension=value,
                    percent_value=imis_product.renewal_discount_perc,
                    period=imis_product.renewal_discount_period
                )
            elif value == "enrolment-discount":
                cls.__build_fhir_discount_extension(
                    extension=extension,
                    type_extension=value,
                    percent_value=imis_product.enrolment_discount_perc,
                    period=imis_product.enrolment_discount_period
                )
            else:
                pass

            if type(fhir_insurance_plan.extension) is not list:
                fhir_insurance_plan.extension = [extension]
            else:
                fhir_insurance_plan.extension.append(extension)

        if imis_product.conversion_product is not None:
            build_extension(fhir_insurance_plan, imis_product.conversion_product, "conversion")
        if imis_product.max_installments is not None:
            build_extension(fhir_insurance_plan, imis_product, "max-installments")
        if imis_product.start_cycle_1 is not None:
            build_extension(fhir_insurance_plan, imis_product, "start_cycle1")
        if imis_product.start_cycle_2 is not None:
            build_extension(fhir_insurance_plan, imis_product, "start_cycle2")
        if imis_product.start_cycle_3 is not None:
            build_extension(fhir_insurance_plan, imis_product, "start_cycle3")
        if imis_product.start_cycle_4 is not None:
            build_extension(fhir_insurance_plan, imis_product, "start_cycle4")
        if imis_product.administration_period is not None:
            build_extension(fhir_insurance_plan, imis_product, "administration-period")
        if imis_product.grace_period_enrolment is not None:
            build_extension(fhir_insurance_plan, imis_product, "payment-grace-period")
        if imis_product.grace_period_renewal is not None:
            build_extension(fhir_insurance_plan, imis_product, "renewal-grace-period")
        if imis_product.renewal_discount_perc is not None and imis_product.renewal_discount_period is not None:
            build_extension(fhir_insurance_plan, imis_product, "renewal-discount")
        if imis_product.enrolment_discount_perc is not None and imis_product.enrolment_discount_period is not None:
            build_extension(fhir_insurance_plan, imis_product, "enrolment-discount")

    @classmethod
    def build_imis_extentions(cls, imis_product, fhir_insurance_plan):
        period_exts = []
        discount_exts = []
        for extension in fhir_insurance_plan.extension:
            if "conversion" in extension.url:
                reference = extension.valueReference.reference
                code = cls.__get_product_code_reference(code=reference)
                products = Product.objects.filter(code=code, validity_to__isnull=True)
                if products:
                    product = products.first()
                    imis_product.conversion_product = product
                else:
                    imis_product.conversion_product = None
            elif "max-installments" in extension.url:
                    imis_product.max_installments = extension.valueUnsignedInt
            # TODO - clarify this period extension and the same for discount extension
            #  it is about handling the same extension object and how to assign values to particular one
            elif "plan-period" in extension.url:
                period_exts.append(extension)
            elif "plan-discount" in extension.url:
                discount_exts.append(extension)
            else:
                pass
        cls.__build_period_extensions(imis_product, period_exts)
        cls.__build_discount_extensions(imis_product, discount_exts)

    @classmethod
    def __build_period_extensions(cls, imis_product, period_exts):
        if len(period_exts) > 0:
            for i in range(len(period_exts)):
                value = period_exts[i].valueQuantity.value
                if i == 0:
                    imis_product.grace_period_enrolment = value
                if i == 1:
                    imis_product.administration_period = value
                if i == 2:
                    imis_product.grace_period_renewal = value

    @classmethod
    def __build_discount_extensions(cls, imis_product, discount_exts):
        if len(discount_exts) > 0:
            for i in range(len(discount_exts)):
                nested_extension = discount_exts[i].extension
                percent_of_discount = None
                period = None
                for ext in nested_extension:
                    if ext.url == "Percentage":
                       percent_of_discount = ext.valueDecimal
                    if ext.url == "Period":
                       period = ext.valueQuantity.value
                if i == 0:
                    imis_product.renewal_discount_perc = percent_of_discount
                    imis_product.renewal_discount_period = period
                if i == 1:
                    imis_product.enrolment_discount_perc = percent_of_discount
                    imis_product.enrolment_discount_period = period

    @classmethod
    def __get_product_code_reference(cls, code):
        return code.rsplit('/', 1)[1]

    @classmethod
    def __build_fhir_cycle(cls, extension, type_extension, start_cycle):
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/insurance-plan-{type_extension[0: -1]}"
        extension.valueString = start_cycle

    @classmethod
    def __build_fhir_period_extension(cls, extension, type_extension, value):
        splited_type = type_extension.split('-')
        index_of_last_element = len(splited_type)-1
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/insurance-plan-{splited_type[index_of_last_element]}"
        extension.valueQuantity = Quantity(
            **{
                "value": value,
                "unit": "months"
            }
        )

    @classmethod
    def __build_fhir_discount_extension(cls, extension, type_extension, percent_value, period):
        splited_type = type_extension.split('-')
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/insurance-plan-{splited_type[1]}"
        nested_extension = Extension.construct()

        # percentage
        nested_extension.url = "Percentage"
        nested_extension.valueDecimal = percent_value
        extension.extension = [nested_extension]

        # period
        nested_extension = Extension.construct()
        nested_extension.url = "Period"
        nested_extension.valueQuantity = Quantity(
            **{
                "value": period,
                "unit": "months"
            }
        )
        extension.extension.append(nested_extension)

    @classmethod
    def _validate_fhir_insurance_plan_identifier_code(cls, fhir_insurance_plan_identifier_code):
        if not fhir_insurance_plan_identifier_code:
            raise FHIRException(
                _('InsurancePlan FHIR without code - this field is obligatory')
            )