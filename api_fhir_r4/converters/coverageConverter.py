from django.utils.translation import gettext
from api_fhir_r4.configurations import R4CoverageConfig
from api_fhir_r4.converters import BaseFHIRConverter, PractitionerConverter, ContractConverter,  ReferenceConverterMixin
from api_fhir_r4.models import Coverage, Reference, Period,Money, Extension, ContractTermAssetValuedItem, \
    ContractTermOfferParty, CoverageClass, ContractTerm, ContractTermAsset, ContractTermOffer
from product.models import ProductItem, ProductService,Product
from policy.models import Policy
from api_fhir_r4.utils import DbManagerUtils,TimeUtils
from insuree.models import Family

class CoverageConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_policy):
        fhir_coverage = Coverage()
        cls.build_coverage_identifier(fhir_coverage, imis_policy)
        cls.build_coverage_policy_holder(fhir_coverage, imis_policy)
        cls.build_coverage_period(fhir_coverage, imis_policy)
        cls.build_coverage_status(fhir_coverage, imis_policy)
        cls.build_coverage_contract(fhir_coverage, imis_policy)
        cls.build_coverage_class(fhir_coverage, imis_policy)
        cls.build_coverage_value(fhir_coverage, imis_policy)
        cls.build_coverage_extension(fhir_coverage, imis_policy)
        return fhir_coverage
    
    @classmethod
    def to_imis_obj(cls,fhir_coverage, audit_user_id):
        imis_policy = Policy()
        errors=[]
        imis_policy.audit_user_id = audit_user_id
        cls.build_imis_status(imis_policy,fhir_coverage,errors)
        cls.build_imis_period(imis_policy,fhir_coverage,errors)
        cls.build_imis_policyholder(imis_policy,fhir_coverage,errors)
        cls.build_imis_class(imis_policy,fhir_coverage,errors)
        cls.check_errors(errors)
        return imis_policy
    
    @classmethod
    def build_imis_product(cls,classes,imis_policy):
        for product in classes:
            coding = cls.get_first_coding_from_codeable_concept(product.type)
            if coding.code  == R4CoverageConfig.get_product_code():
                imis_policy.product = Product.objects.get(uuid=product.id)
                imis_policy.value = product.value
                      
    @classmethod
    def build_imis_status(cls, imis_policy,fhir_coverage,errors):
        status = fhir_coverage.status
        if not cls.valid_condition(status is None, gettext('Missing  `status` attribute'),errors):
            if status =='active':
                imis_policy.status =2
            else:
                imis_policy.status=1

    @classmethod
    def build_imis_class(cls, imis_policy,fhir_coverage,errors):
        product = fhir_coverage.classes
        if not cls.valid_condition(product is None, gettext('Missing  `class` attribute'),errors):
            cls.build_imis_product(product,imis_policy)
            
    @classmethod
    def build_imis_policyholder(cls,imis_policy,fhir_coverage,errors):
        policyholder = fhir_coverage.policyHolder
        if not cls.valid_condition(policyholder is None, gettext('Missing  `policy holder` attribute'),errors):
            if not cls.valid_condition(policyholder.reference is None, gettext('Missing  `policyholder reference` attribute'),errors):
                reference = policyholder.reference .split("/", 2)
                obj=Family.objects.get(uuid=reference[1])
                imis_policy.family = obj
            
    @classmethod
    def build_imis_period(cls, imis_policy,fhir_coverage,errors):
        period = fhir_coverage.period
        if not cls.valid_condition(period is None, gettext('Missing  `period` attribute'),errors):
            if not cls.valid_condition(period.start is None, gettext('Missing  `period start` attribute'),errors):
                imis_policy.start_date = TimeUtils.str_to_date(period.start) 
                imis_policy.enroll_date = TimeUtils.str_to_date(period.start) 
                imis_policy.effective_date = TimeUtils.str_to_date(period.start) 
            if not cls.valid_condition(period.end is None, gettext('Missing  `period end` attribute'),errors):
                imis_policy.expiry_date = TimeUtils.str_to_date(period.end)
            # imis_policy.status = fhir_coverage.status    
    @classmethod
    def get_reference_obj_id(cls, imis_policy):
        return imis_policy.uuid

    @classmethod
    def get_fhir_resource_type(cls):
        return Coverage

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_policy_code = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Policy, code=imis_policy_code)

    @classmethod
    def build_coverage_identifier(cls, fhir_coverage, imis_policy):
        identifiers = []
        cls.build_fhir_uuid_identifier(identifiers, imis_policy)
        fhir_coverage.identifier = identifiers
        return fhir_coverage

    @classmethod
    def build_coverage_policy_holder(cls, fhir_coverage, imis_policy):
        reference = Reference()
        resource_type = R4CoverageConfig.get_family_reference_code()
        resource_id = imis_policy.family.uuid
        reference.reference = resource_type + '/' + str(resource_id)
        fhir_coverage.policyHolder = reference
        return fhir_coverage

    @classmethod
    def build_coverage_period(cls, fhir_coverage, imis_policy):
        period = Period()
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
    def build_coverage_value(cls, fhir_coverage, imis_policy):
        fhir_coverage.value = imis_policy.value
        return fhir_coverage

    @classmethod
    def build_coverage_contract(cls, fhir_coverage, imis_coverage):
        reference = ContractConverter.build_fhir_resource_reference(imis_coverage)
        fhir_coverage.contract.append(reference)
        return fhir_coverage

    @classmethod
    def build_contract_valued_item(self, contract, imis_coverage):
        valued_item = ContractTermAssetValuedItem()
        policy_value = Money()
        policy_value.value = imis_coverage.value
        valued_item.net = policy_value
        if contract.term is None:
            contract.term = [ContractTerm()]
        elif len(contract.term) == 0:
            contract.term.append(ContractTerm())
        if contract.term[0].asset is None:
            contract.term[0].asset = [ContractTermAsset()]
        elif len(contract.term[0].asset) == 0:
            contract.term[0].asset.append(ContractTermAsset())
        contract.term[0].asset[0].valuedItem.append(valued_item)
        return contract

    @classmethod
    def build_contract_party(cls, contract, imis_coverage):
        if imis_coverage.officer is not None:
            party = ContractTermOfferParty()
            reference = PractitionerConverter.build_fhir_resource_reference(imis_coverage.officer)
            party.reference.append(reference)
            if contract.term is None:
                contract.term.append[ContractTerm()]
            elif len(contract.term) == 0:
                contract.term.append(ContractTerm())
            if contract.term[0].offer is None:
                contract.term[0].offer = ContractTermOffer()
            provider_role = cls.build_simple_codeable_concept(R4CoverageConfig.get_practitioner_role_code())
            party.role = provider_role
            contract.term[0].offer.party.append(party)

    @classmethod
    def build_coverage_class(cls, fhir_coverage, imis_coverage):
        class_ = CoverageClass()
        product = imis_coverage.product
        class_.type = R4CoverageConfig.get_product_code() + "/" + str(product.uuid)
        class_.name = product.code

        cls.__build_product_plan_display(class_, product)
        fhir_coverage.classes = [class_]

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
        fhir_coverage.extension.append(enroll_date)

    @classmethod
    def __build_enroll_date(cls, fhir_coverage, imis_coverage):
        enroll_date = cls.__build_date_extension(imis_coverage.enroll_date,
                                                 R4CoverageConfig.get_enroll_date_code())
        fhir_coverage.extension.append(enroll_date)

    @classmethod
    def __build_date_extension(cls, value, name):
        ext_date = Extension()
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
        class_.type = product.name
        class_.name = str(product_coverage)
