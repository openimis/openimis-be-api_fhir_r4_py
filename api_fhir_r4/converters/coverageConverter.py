from django.utils.translation import gettext as _
from api_fhir_r4.configurations import GeneralConfiguration, R4CoverageConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.mapping.coverageMapping import CoverageStatus
from api_fhir_r4.models import CoverageV2 as Coverage, CoverageClassV2 as CoverageClass
from fhir.resources.period import Period
from fhir.resources.extension import Extension
from fhir.resources.reference import Reference
from policy.signals import signal_check_formal_sector_for_policy
from product.models import ProductItem, ProductService
from policy.models import Policy
from api_fhir_r4.utils import TimeUtils


class CoverageConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_policy, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_coverage = Coverage.construct()
        cls.build_coverage_status(fhir_coverage, imis_policy)
        cls.build_coverage_identifier(fhir_coverage, imis_policy)
        cls.build_coverage_policy_holder(fhir_coverage, imis_policy)
        cls.build_coverage_period(fhir_coverage, imis_policy)
        cls.build_coverage_class(fhir_coverage, imis_policy)
        cls.build_coverage_beneficiary(fhir_coverage, imis_policy)
        cls.build_coverage_payor(fhir_coverage, imis_policy)
        cls.build_coverage_extension(fhir_coverage, imis_policy)
        return fhir_coverage
 
    @classmethod
    def get_reference_obj_uuid(cls, imis_policy: Policy):
        return imis_policy.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_policy: Policy):
        return imis_policy.id

    @classmethod
    def get_reference_obj_code(cls, imis_policy: Policy):
        # Policy doesn't have code representation, uuid is used instead
        return imis_policy.uuid

    @classmethod
    def build_fhir_code_identifier(cls, identifiers, imis_object):
        # Policy doesn't have code representation, uuid is used instead
        cls.build_fhir_uuid_identifier(identifiers, imis_object)

    @classmethod
    def get_fhir_resource_type(cls):
        return Coverage

    @classmethod
    def build_coverage_identifier(cls, fhir_coverage, imis_policy):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_policy)
        fhir_coverage.identifier = identifiers
        return fhir_coverage

    @classmethod
    def build_all_identifiers(cls, identifiers, imis_object):
        # Coverage don't have code
        cls.build_fhir_uuid_identifier(identifiers, imis_object)
        cls.build_fhir_id_identifier(identifiers, imis_object)
        return identifiers

    @classmethod
    def build_coverage_policy_holder(cls, fhir_coverage, imis_policy):
        reference = Reference.construct()
        resource_id = imis_policy.family.head_insuree.chf_id
        reference.reference = f'Patient/{str(resource_id)}'
        fhir_coverage.policyHolder = reference
        return fhir_coverage

    @classmethod
    def build_coverage_beneficiary(cls, fhir_coverage, imis_policy):
        reference = Reference.construct()
        resource_id = imis_policy.family.head_insuree.chf_id
        reference.reference = f'Patient/{str(resource_id)}'
        fhir_coverage.beneficiary = reference
        return fhir_coverage

    @classmethod
    def build_coverage_payor(cls, fhir_coverage, imis_policy):
        policy_holder_contract = None
        # send the signal from policy module - check if policy is connected to
        # formal sector contract entity
        results_signal_policy_fs = signal_check_formal_sector_for_policy.send(
             sender=cls, policy_id=imis_policy.id
        )
        if len(results_signal_policy_fs) > 0:
            if results_signal_policy_fs[0][1]:
                policy_holder_contract = results_signal_policy_fs[0][1]
        if policy_holder_contract:
            # formal sector
            resource_id = policy_holder_contract.id
            resource_type = 'Organization'
        else:
            # informal sector
            resource_id = imis_policy.family.head_insuree.chf_id
            resource_type = 'Patient'

        fhir_coverage.payor = []
        reference = Reference.construct()
        reference.reference = f'{resource_type}/{resource_id}'
        fhir_coverage.payor.append(reference)
        return fhir_coverage

    @classmethod
    def build_coverage_period(cls, fhir_coverage, imis_policy):
        period = Period.construct()
        if imis_policy.start_date is not None:
            period.start = imis_policy.start_date.isoformat()
        if imis_policy.expiry_date is not None:
            period.end = imis_policy.expiry_date.isoformat()
        fhir_coverage.period = period
        return period

    @classmethod
    def build_coverage_status(cls, fhir_coverage, imis_policy):
        code = imis_policy.status
        fhir_coverage.status = CoverageStatus.map_status(code)
        return fhir_coverage

    @classmethod
    def build_coverage_class(cls, fhir_coverage, imis_coverage):
        fhir_coverage.class_fhir = []

        coverage_class = CoverageClass.construct()
        product = imis_coverage.product
        coverage_class.value = product.code
        coverage_class.name = product.name
        coverage_class.type = cls.build_codeable_concept(
            system='http://terminology.hl7.org/CodeSystem/coverage-class',
            code='plan',
            display=_('Plan')
        )

        fhir_coverage.class_fhir.append(coverage_class)

    @classmethod
    def build_coverage_extension(cls, fhir_coverage, imis_coverage):
        cls.__build_enroll_date(fhir_coverage, imis_coverage)
        cls.__build_effective_date(fhir_coverage, imis_coverage)
        return fhir_coverage

    @classmethod
    def __build_effective_date(cls, fhir_coverage, imis_coverage):
        enroll_date = cls.__build_date_extension(imis_coverage.effective_date)
        if type(fhir_coverage.extension) is not list:
            fhir_coverage.extension = [enroll_date]
        else:
            fhir_coverage.extension.append(enroll_date)

    @classmethod
    def __build_enroll_date(cls, fhir_coverage, imis_coverage):
        enroll_date = cls.__build_date_extension(imis_coverage.enroll_date)
        if type(fhir_coverage.extension) is not list:
            fhir_coverage.extension = [enroll_date]
        else:
            fhir_coverage.extension.append(enroll_date)

    @classmethod
    def __build_date_extension(cls, value):
        ext_date = Extension.construct()
        ext_date.url = f'{GeneralConfiguration.get_system_base_url()}/StructureDefinition/coverage-date'
        ext_date.valueDate = TimeUtils.str_to_date(value.isoformat())
        return ext_date

    @classmethod
    def __build_product_plan_display(cls, class_, product):
        product_coverage = {}
        service_code = R4CoverageConfig.get_service_code()
        item_code = R4CoverageConfig.get_item_code()
        product_items = ProductItem.objects.filter(product=product).all()
        product_services = ProductService.objects.filter(product=product).all()
        product_coverage[item_code] = [item.item.code for item in product_items]
        product_coverage[service_code] = [service.service.code for service in product_services]
        class_.value = product.code
        class_.type = cls.build_simple_codeable_concept(product.name)
        class_.name = str(product_coverage)
