from django.utils.translation import gettext
from api_fhir_r4.configurations import R4CoverageConfig
from api_fhir_r4.converters import BaseFHIRConverter, PractitionerConverter, ContractConverter,  ReferenceConverterMixin
from api_fhir_r4.models import CoverageV2 as Coverage, CoverageClassV2 as CoverageClass
from fhir.resources.money import Money
from fhir.resources.period import Period
from fhir.resources.extension import Extension
from fhir.resources.reference import Reference
from fhir.resources.contract import ContractTermAssetValuedItem, ContractTermOfferParty, ContractTerm, ContractTermAsset, ContractTermOffer
from product.models import ProductItem, ProductService, Product
from policy.models import Policy
from api_fhir_r4.utils import DbManagerUtils, TimeUtils
from insuree.models import Family


class CoverageConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_policy, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_coverage = Coverage.construct()
        cls.build_coverage_status(fhir_coverage, imis_policy)
        cls.build_coverage_identifier(fhir_coverage, imis_policy)
        cls.build_coverage_policy_holder(fhir_coverage, imis_policy)
        cls.build_coverage_period(fhir_coverage, imis_policy)
        cls.build_coverage_contract(fhir_coverage, imis_policy, reference_type)
        cls.build_coverage_class(fhir_coverage, imis_policy)
        #cls.build_coverage_value(fhir_coverage, imis_policy)
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
        return imis_policy.code

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
        resource_type = R4CoverageConfig.get_family_reference_code()
        resource_id = imis_policy.family.uuid
        reference.reference = resource_type + '/' + str(resource_id)
        fhir_coverage.policyHolder = reference
        return fhir_coverage

    @classmethod
    def build_coverage_beneficiary(cls, fhir_coverage, imis_policy):
        reference = Reference.construct()
        resource_type = R4CoverageConfig.get_family_reference_code()
        resource_id = imis_policy.family.uuid
        reference.reference = resource_type + '/' + str(resource_id)
        fhir_coverage.beneficiary = reference
        return fhir_coverage

    @classmethod
    def build_coverage_payor(cls, fhir_coverage, imis_policy):
        reference = Reference.construct()
        organization = R4CoverageConfig.get_organization_code()
        reference.reference = "Organization/" + str(organization)
        if type (fhir_coverage.payor) is not list:
            fhir_coverage.payor = [reference]
        else:
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
        fhir_coverage.status = cls.__map_status(code)
        return fhir_coverage

    @classmethod
    def build_coverage_contract(cls, fhir_coverage, imis_coverage, reference_type):
        reference = ContractConverter.build_fhir_resource_reference(imis_coverage, reference_type=reference_type)
        if type(fhir_coverage.contract) is not list:
            fhir_coverage.contract = [reference]
        else:
            fhir_coverage.contract.append(reference)
        return fhir_coverage

    @classmethod
    def build_coverage_value(cls, fhir_coverage, imis_policy):
        fhir_coverage.value = imis_policy.value
        return fhir_coverage

    @classmethod
    def build_contract_valued_item(self, contract, imis_coverage):
        valued_item = ContractTermAssetValuedItem.construct()
        policy_value = Money.construct()
        policy_value.value = imis_coverage.value
        valued_item.net = policy_value
        if contract.term is None:
            contract.term = [ContractTerm.construct()]
        elif len(contract.term) == 0:
            contract.term.append(ContractTerm.construct())
        if contract.term[0].asset is None:
            contract.term[0].asset = [ContractTermAsset.construct()]
        elif len(contract.term[0].asset) == 0:
            contract.term[0].asset.append(ContractTermAsset.construct())
        contract.term[0].asset[0].valuedItem.append(valued_item)
        return contract

    @classmethod
    def build_contract_party(cls, contract, imis_coverage, reference_type):
        if imis_coverage.officer is not None:
            party = ContractTermOfferParty.construct()
            reference = PractitionerConverter\
                .build_fhir_resource_reference(imis_coverage.officer, reference_type=reference_type)
            party.reference.append(reference)
            if contract.term is None:
                contract.term.append[ContractTerm.construct()]
            elif len(contract.term) == 0:
                contract.term.append(ContractTerm.construct())
            if contract.term[0].offer is None:
                contract.term[0].offer = ContractTermOffer.construct()
            provider_role = cls.build_simple_codeable_concept(R4CoverageConfig.get_practitioner_role_code())
            party.role = provider_role
            contract.term[0].offer.party.append(party)

    @classmethod
    def build_coverage_class(cls, fhir_coverage, imis_coverage):
        class_ = CoverageClass.construct()
        product = imis_coverage.product
        class_.value = product.code
        class_.type = cls.build_simple_codeable_concept(R4CoverageConfig.get_product_code() + "/" + str(product.uuid))
        class_.name = product.code

        cls.__build_product_plan_display(class_, product)
        if type(fhir_coverage.class_fhir) is not list:
            fhir_coverage.class_fhir = [class_]
        else:
            fhir_coverage.class_fhir.append(class_)

    @classmethod
    def __map_status(cls, code):
        codes = {
            1: R4CoverageConfig.get_status_idle_code(),
            2: R4CoverageConfig.get_status_active_code(),
            4: R4CoverageConfig.get_status_suspended_code(),
            8: R4CoverageConfig.get_status_expired_code(),
        }
        return codes[code]

    @classmethod
    def build_coverage_extension(cls, fhir_coverage, imis_coverage):
        cls.__build_effective_date(fhir_coverage, imis_coverage)
        cls.__build_enroll_date(fhir_coverage, imis_coverage)
        return fhir_coverage

    @classmethod
    def __build_effective_date(cls, fhir_coverage, imis_coverage):
        enroll_date = cls.__build_date_extension(imis_coverage.effective_date,
                                                 R4CoverageConfig.get_effective_date_code())
        if type(fhir_coverage.extension) is not list:
            fhir_coverage.extension = [enroll_date]
        else:
            fhir_coverage.extension.append(enroll_date)

    @classmethod
    def __build_enroll_date(cls, fhir_coverage, imis_coverage):
        enroll_date = cls.__build_date_extension(imis_coverage.enroll_date,
                                                 R4CoverageConfig.get_enroll_date_code())
        if type(fhir_coverage.extension) is not list:
            fhir_coverage.extension = [enroll_date]
        else:
            fhir_coverage.extension.append(enroll_date)

    @classmethod
    def __build_date_extension(cls, value, name):
        ext_date = Extension.construct()
        ext_date.url = name
        ext_date.valueDate = value.isoformat() if value else None
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
