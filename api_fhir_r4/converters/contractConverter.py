from api_fhir_r4.configurations import R4CoverageConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.models import  Reference,  Contract, Money, Extension, Period,\
     ContractTermAssetContext, ContractTermAssetValuedItem,  ContractTerm, ContractTermAsset, ContractTermOffer,ContractSigner
from product.models import ProductItem, ProductService
from policy.models import Policy
from insuree.models import InsureePolicy
from api_fhir_r4.utils import DbManagerUtils


class ContractConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_policy):
        fhir_contract = Contract()
        cls.build_contract_identifier(fhir_contract, imis_policy)
        contractTerm = ContractTerm()
        contractTermAsset = ContractTermAsset()
        cls.build_contract_asset_context(contractTermAsset, imis_policy)
        cls.build_contract_valued_item(contractTermAsset, imis_policy)
        cls.build_contract_asset_type_reference(contractTermAsset, imis_policy)
        cls.build_contract_asset_use_period(contractTermAsset, imis_policy)
        contractTerm.asset = [contractTermAsset]
        fhir_contract.term = [contractTerm]
        cls.build_contract_status(fhir_contract, imis_policy)
        cls.build_contract_signer(fhir_contract, imis_policy)
        cls.build_contract_state(fhir_contract, imis_policy)
        return fhir_contract

    @classmethod
    def get_reference_obj_id(cls, imis_policy):
        return imis_policy.uuid

    @classmethod
    def get_fhir_resource_type(cls):
        return Contract

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_policy_code = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Policy, code=imis_policy_code)

    @classmethod
    def build_contract_identifier(cls, fhir_contract, imis_policy):
        identifiers = []
        cls.build_fhir_uuid_identifier(identifiers, imis_policy)
        fhir_contract.identifier = identifiers
        return fhir_contract

 
    @classmethod
    def build_contract_valued_item(cls, contract_asset, imis_policy):
        valued_item = ContractTermAssetValuedItem()
        policy_value = Money()
        policy_value.value = imis_policy.value
        valued_item.net = policy_value
        contract_asset.valuedItem.append(valued_item)
        return contract_asset

    @classmethod
    def build_contract_asset_use_period(cls, contract_asset, imis_policy):
        period_use = Period()
        period= Period()
        if imis_policy.start_date is not None:
            period.start = imis_policy.start_date.strftime("%Y-%m-%d")
            period_use.start = period.start
        if imis_policy.effective_date is not None:
            period_use.start = imis_policy.effective_date.strftime("%Y-%m-%d")
            if period_use.start is None:
                period.start = period_use.start
        if imis_policy.expiry_date is not None:
            period_use.end = imis_policy.expiry_date.strftime("%Y-%m-%d")
            period.end = period_use.end

        contract_asset.usePeriod = [period_use]
        contract_asset.period = [period]
        return contract_asset

    @classmethod
    def build_contract_asset_context(cls, contract_term_asset, imis_policy):
        insureePolicies = imis_policy.insuree_policies.all()
        for insureePolicy in insureePolicies:
            if insureePolicy.insuree.head is True:
                party_role = cls.build_simple_codeable_concept(R4CoverageConfig.get_offer_insuree_role_code())
            else:
                party_role = cls.build_simple_codeable_concept(R4CoverageConfig.get_offer_dependant_role_code())

            assetContext = ContractTermAssetContext()
            assetContext.code = [party_role]
            display = insureePolicy.insuree.uuid + ":" + imis_policy.family.location.code # used for the DHIS integration
            assetContext.reference = cls.build_fhir_resource_reference(insureePolicy.insuree, "Patient",display)
            if contract_term_asset.context is None:
                contract_term_asset.context = [assetContext]
            else:
                contract_term_asset.context.append(assetContext)
        return contract_term_asset
        
    @classmethod
    def build_contract_status(cls, contract, imis_policy):
        if  imis_policy.status is imis_policy.STATUS_ACTIVE:
            contract.status = R4CoverageConfig.get_status_policy_code()
        elif  imis_policy.status is imis_policy.STATUS_IDLE:
            contract.status = R4CoverageConfig.get_status_offered_code()
        elif  imis_policy.status is imis_policy.STATUS_EXPIRED:
            contract.status = R4CoverageConfig.get_status_terminated_code()
        elif  imis_policy.status is imis_policy.STATUS_SUSPENDED:
            contract.status = R4CoverageConfig.get_status_disputed_code()
        else:
            contract.status = imis_policy.status
        return contract

    @classmethod
    def build_contract_state(cls, contract, imis_policy):
        if  imis_policy.stage is imis_policy.STAGE_NEW:
            contract.legalState = cls.build_simple_codeable_concept(R4CoverageConfig.get_status_offered_code())
        elif  imis_policy.stage is imis_policy.STAGE_RENEWED:
            contract.legalState = cls.build_simple_codeable_concept(R4CoverageConfig.get_status_renewed_code())
        else:
            contract.legalState = cls.build_simple_codeable_concept(imis_policy.stage)
        return contract

    @classmethod
    def build_contract_asset_type_reference(cls, contract_asset, imis_policy):
        typeReference = cls.build_fhir_resource_reference(imis_policy.product, "InsurancePlan", imis_policy.product.code )
        contract_asset.typeReference = [typeReference]
        return contract_asset

    @classmethod
    def build_contract_signer(cls, contract, imis_policy):
        if imis_policy.officer is not None:
            reference = cls.build_fhir_resource_reference(imis_policy.officer, "Practitioner")
            signer = ContractSigner()
            signer.party = reference
            eo_type = cls.build_simple_codeable_concept(R4CoverageConfig.get_signer_eo_type_code())
            signer.type = eo_type
            if contract.signer is None:
                contract.signer = signer
            else :
                contract.signer.append(signer)
        if imis_policy.family is not None:
            if imis_policy.family.head_insuree is not None:
                reference = cls.build_fhir_resource_reference(imis_policy.family.head_insuree, "Patient")
                signer = ContractSigner()
                signer.party = reference
                eo_type = cls.build_simple_codeable_concept(R4CoverageConfig.get_signer_head_type_code())
                signer.type = eo_type
                if contract.signer is None:
                    contract.signer = signer
                else :
                    contract.signer.append(signer)            
