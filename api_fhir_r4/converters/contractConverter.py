import core

from django.db.models import Q
from django.utils.translation import gettext as _
from api_fhir_r4.configurations import GeneralConfiguration, R4CoverageConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.converters.patientConverter import PatientConverter
from api_fhir_r4.mapping.contractMapping import PayTypeMapping, ContractStatus, \
    ContractState
from fhir.resources.contract import Contract, ContractTermAssetValuedItem, \
    ContractTerm, ContractTermAsset, ContractTermOffer, ContractTermOfferParty
from fhir.resources.extension import Extension
from fhir.resources.money import Money
from fhir.resources.period import Period

from product.models import Product
from policy.models import Policy
from insuree.models import Insuree, InsureePolicy
from insuree.models import Family
from contribution.models import Premium
from core.models import Officer
from api_fhir_r4.utils import DbManagerUtils, TimeUtils


class ContractConverter(BaseFHIRConverter, ReferenceConverterMixin):
    @classmethod
    def to_fhir_obj(cls, imis_policy, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_contract = Contract.construct()
        cls.build_contract_identifier(fhir_contract, imis_policy)
        cls.build_contract_author(fhir_contract, imis_policy, reference_type)
        cls.build_contract_subject(fhir_contract, imis_policy, reference_type)
        cls.build_contract_scope(fhir_contract, imis_policy)
        contract_term = ContractTerm.construct()
        cls.build_contract_term_offer(contract_term, imis_policy, reference_type)
        contract_term_asset = ContractTermAsset.construct()
        cls.build_contract_asset_extension(contract_term_asset, imis_policy, reference_type)
        cls.build_contract_asset_type_reference(contract_term_asset, imis_policy, reference_type)
        cls.build_contract_valued_item_entity(contract_term_asset, imis_policy)
        cls.build_contract_asset_use_period(contract_term_asset, imis_policy)
        contract_term.asset = [contract_term_asset]
        fhir_contract.term = [contract_term]
        cls.build_contract_status(fhir_contract, imis_policy)
        cls.build_contract_state(fhir_contract, imis_policy)
        return fhir_contract

    @classmethod
    def to_imis_obj(cls,fhir_contract, audit_user_id):
        errors = []
        fhir_contract = Contract(**fhir_contract)
        imis_policy = Policy()
        imis_policy.audit_user_id = audit_user_id
        cls.build_imis_period(imis_policy, fhir_contract.term, errors)
        cls.build_imis_useperiod(imis_policy, fhir_contract.term, errors)
        cls.build_imis_status(fhir_contract,imis_policy, errors)
        cls.build_imis_author(fhir_contract, imis_policy, errors)
        cls.build_imis_subject(fhir_contract, imis_policy, errors)
        cls.build_imis_product(fhir_contract, imis_policy, errors)
        cls.build_imis_state(fhir_contract, imis_policy, errors)
        cls.build_imis_insurees(fhir_contract, imis_policy, errors)
        cls.build_imis_contributions(fhir_contract, imis_policy, errors)
        cls.check_errors(errors)
        return imis_policy

    @classmethod
    def get_reference_obj_uuid(cls, imis_policy: Policy):
        return imis_policy.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_policy: Policy):
        return imis_policy.id


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
        cls.build_all_identifiers(identifiers, imis_policy)
        fhir_contract.identifier = identifiers
        return fhir_contract

    @classmethod
    def build_all_identifiers(cls, identifiers, imis_object):
        # Coverage have only uuid coverage
        cls.build_fhir_uuid_identifier(identifiers, imis_object)
        cls.build_fhir_id_identifier(identifiers, imis_object)
        return identifiers

    @classmethod
    def build_contract_author(cls, fhir_contract, imis_policy, reference_type):
        author = cls.build_fhir_resource_reference(
            imis_policy.officer, "Practitioner", imis_policy.officer.code, reference_type=reference_type)
        fhir_contract.author = author

    @classmethod
    def build_contract_subject(cls, fhir_contract, imis_policy, reference_type):
        subject = cls.build_fhir_resource_reference(
            imis_policy.family, "Group", imis_policy.family.head_insuree.last_name, reference_type=reference_type)
        fhir_contract.subject = [subject]

    @classmethod
    def build_contract_scope(cls, fhir_contract, imis_policy):
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/contract-scope"
        fhir_contract.scope = cls.build_codeable_concept(code="informal", system=system)
        if len(fhir_contract.scope.coding) == 1:
            fhir_contract.scope.coding[0].display = _("Informal Sector")

    @classmethod
    def build_contract_asset_extension(cls, contract_term_asset, imis_policy, reference_type):
        cls.build_contract_asset_premium(contract_term_asset, imis_policy)

    @classmethod
    def build_contract_asset_premium(cls, contract_term_asset, imis_policy):
        asset_extensions = Extension.construct()
        asset_extensions.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/contract-premium"
        if Premium.objects.filter(policy=imis_policy, validity_to__isnull=True).count() > 0:
            imis_premium = Premium.objects.get(policy=imis_policy, validity_to__isnull=True)
            fhir_premium = cls.build_contract_asset_premium_extension(asset_extensions, imis_premium)
            if type(contract_term_asset.extension) is not list:
                contract_term_asset.extension = [fhir_premium]
            else:
                contract_term_asset.extension.append(fhir_premium)

    @classmethod
    def build_contract_asset_premium_extension(cls, asset_extensions, imis_premium):
        cls.build_premium_payer_ext(asset_extensions)
        cls.build_premium_category_ext(asset_extensions)
        cls.build_premium_amount_ext(asset_extensions, imis_premium)
        cls.build_premium_receipt_ext(asset_extensions, imis_premium)
        cls.build_premium_date_ext(asset_extensions, imis_premium)
        cls.build_premium_type_ext(asset_extensions, imis_premium)
        return asset_extensions

    @classmethod
    def build_premium_payer_ext(cls, asset_extensions):
        extension = Extension.construct()
        extension.url = "payer"
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/contract-premium-payer"
        extension.valueCodeableConcept = cls.build_codeable_concept(code="beneficiary", system=system)
        if len(extension.valueCodeableConcept.coding) == 1:
            extension.valueCodeableConcept.coding[0].display = _("Beneficiary")
        asset_extensions.extension = [extension]

    @classmethod
    def build_premium_category_ext(cls, asset_extensions):
        extension = Extension.construct()
        extension.url = "category"
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/contract-premium-category"
        extension.valueCodeableConcept = cls.build_codeable_concept(code="C", system=system)
        if len(extension.valueCodeableConcept.coding) == 1:
            extension.valueCodeableConcept.coding[0].display = _("Contribution and Others")
        asset_extensions.extension.append(extension)

    @classmethod
    def build_premium_amount_ext(cls, asset_extensions, imis_premium):
        # get the currency defined in configs from core module
        if hasattr(core, 'currency'):
            currency = core.currency
        else:
            currency = "EUR"

        extension = Extension.construct()
        extension.url = "amount"
        money = Money(**{
            "value": imis_premium.amount,
            "currency": currency
        })
        extension.valueMoney = money
        asset_extensions.extension.append(extension)

    @classmethod
    def build_premium_receipt_ext(cls, asset_extensions, imis_premium):
        extension = Extension.construct()
        extension.url = "receipt"
        extension.valueString = imis_premium.receipt
        asset_extensions.extension.append(extension)

    @classmethod
    def build_premium_date_ext(cls, asset_extensions, imis_premium):
        extension = Extension.construct()
        extension.url = "date"
        extension.valueDate = imis_premium.pay_date
        asset_extensions.extension.append(extension)

    @classmethod
    def build_premium_type_ext(cls, asset_extensions, imis_premium):
        extension = Extension.construct()
        extension.url = "type"
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/contract-premium-type"
        extension.valueCodeableConcept = cls.build_codeable_concept(code=imis_premium.pay_type, system=system)
        if len(extension.valueCodeableConcept.coding) == 1:
            extension.valueCodeableConcept.coding[0].display = PayTypeMapping.pay_type[imis_premium.pay_type]
        asset_extensions.extension.append(extension)

    @classmethod
    def build_contract_asset_use_period(cls, contract_asset, imis_policy):
        period_use = Period.construct()
        period = Period.construct()
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

        if type(contract_asset.usePeriod) is not list:
            contract_asset.usePeriod = [period_use]
        else:
            contract_asset.usePeriod.append(period_use)
        if type(contract_asset.period) is not list:
            contract_asset.period = [period]
        else:
            contract_asset.period.append(period)
        return contract_asset

    @classmethod
    def build_contract_term_offer(cls, contract_term_offer, imis_policy, reference_type):
        offer = ContractTermOffer.construct()

        offer_party = ContractTermOfferParty.construct()
        offer_party.reference = [PatientConverter.build_fhir_resource_reference(imis_policy.family.head_insuree, 'Patient')]
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/contract-resource-party-role"
        offer_party.role = cls.build_codeable_concept(code="beneficiary", system=system)
        if len(offer_party.role.coding) == 1:
            offer_party.role.coding[0].display = _("Beneficiary")

        offer.party = [offer_party]
        contract_term_offer.offer = offer

    @classmethod
    def build_contract_status(cls, contract, imis_policy):
        if f"{imis_policy.status}" in ContractStatus.contract_status:
            contract.status = ContractStatus.contract_status[f"{imis_policy.status}"]
        else:
            contract.status = imis_policy.status
        return contract

    @classmethod
    def build_contract_state(cls, contract, imis_policy):
        if f"{imis_policy.stage}" in ContractState.contract_state:
            contract.legalState = cls.build_simple_codeable_concept(ContractState.contract_state[f"{imis_policy.stage}"])
        else:
            contract.legalState = cls.build_simple_codeable_concept(imis_policy.stage)
        return contract

    @classmethod
    def build_contract_valued_item_entity(cls, contract_asset, imis_policy):
        valued_item = ContractTermAssetValuedItem.construct()
        typeReference = cls.build_fhir_resource_reference(imis_policy.product, "InsurancePlan", imis_policy.product.code)
        valued_item.entityReference = typeReference
        policy_value = Money.construct()
        policy_value.value = imis_policy.value
        valued_item.net = policy_value
        if type(contract_asset.valuedItem) is not list:
            contract_asset.valuedItem = [valued_item]
        else:
            contract_asset.valuedItem.append(valued_item)
        return contract_asset

    @classmethod
    def build_contract_asset_type_reference(cls, contract_asset, imis_policy, reference_type):
        # type reference - take insurees covered as a policy patient
        from core import datetime
        now = datetime.datetime.now()

        list_insuree_policy = InsureePolicy.objects.filter(
            Q(policy=imis_policy),
            Q(validity_from__lte=now),
            Q(validity_to__isnull=True) | Q(validity_to__gte=now),
        ).only('insuree')

        for insuree_policy in list_insuree_policy:
            insuree = insuree_policy.insuree
            type_reference = cls.build_fhir_resource_reference(
                insuree, "Patient", insuree.chf_id, reference_type=reference_type
            )
            if type(contract_asset.typeReference) is not list:
                contract_asset.typeReference = [type_reference]
            else:
                contract_asset.typeReference.append(type_reference)

        return contract_asset

    @classmethod
    def build_imis_period(cls, imis_policy, fhir_contract, errors):
        for term in fhir_contract:
            if term.asset:
                for asset in term.asset:
                    if asset.period:
                        for period in asset.period:
                            if not cls.valid_condition(period.start is None, _('Missing  `period start` attribute'),errors):
                                imis_policy.start_date = TimeUtils.str_to_date(period.start)
                                imis_policy.enroll_date = TimeUtils.str_to_date(period.start)
                            if not cls.valid_condition(period.end is None, _('Missing  `period end` attribute'),errors):
                                imis_policy.expiry_date = TimeUtils.str_to_date(period.end)
                    else:
                        cls.valid_condition(not asset.period, _('Missing  `period` attribute'),errors)

    @classmethod
    def build_imis_useperiod(cls, imis_policy,fhir_contract,errors):
        for term in  fhir_contract:
            if term.asset:
                for asset in term.asset:
                    if asset.usePeriod:
                        for period in asset.usePeriod:
                            if not cls.valid_condition(period.start is None, _('Missing  `usePeriod start` attribute'),errors):
                                imis_policy.effective_date = TimeUtils.str_to_date(period.start)
                            if not cls.valid_condition(period.end is None, _('Missing  `usePeriod end` attribute'),errors):
                                imis_policy.expiry_date = TimeUtils.str_to_date(period.end)
                    else:
                        cls.valid_condition(not asset.usePeriod, _('Missing  `usePeriod` attribute'),errors)

    @classmethod
    def build_imis_status(cls, fhir_contract, imis_policy,errors):
        if fhir_contract.status:
            if fhir_contract.status == R4CoverageConfig.get_status_idle_code():
                imis_policy.status = ContractStatus.imis_map_status(R4CoverageConfig.get_status_idle_code(), imis_policy)
            elif fhir_contract.status == R4CoverageConfig.get_status_active_code():
                imis_policy.status = ContractStatus.imis_map_status(R4CoverageConfig.get_status_active_code(), imis_policy)
            elif fhir_contract.status == R4CoverageConfig.get_status_suspended_code():
                 imis_policy.status = ContractStatus.imis_map_status(R4CoverageConfig.get_status_suspended_code(), imis_policy)
            elif fhir_contract.status == R4CoverageConfig.get_status_expired_code():
                 imis_policy.status = ContractStatus.imis_map_status(R4CoverageConfig.get_status_expired_code(), imis_policy)
            else:
                imis_policy.status = ContractStatus.imis_map_status(R4CoverageConfig.get_status_idle_code(), imis_policy)
        else:
            cls.valid_condition(fhir_contract.status is None, _('Missing  `status` attribute'),errors)

    @classmethod
    def build_imis_author(cls, fhir_contract, imis_policy, errors):
        if fhir_contract.author:
            reference = fhir_contract.author.reference.split("Practitioner/", 2)
            imis_policy.officer = Officer.objects.get(uuid=reference[1])
        else:
            cls.valid_condition(not fhir_contract.author, _('Missing  `author` attribute'), errors)

    @classmethod
    def build_imis_subject(cls, fhir_contract, imis_policy, errors):
        if fhir_contract.subject:
            for subject in  fhir_contract.subject:
                if subject.reference is not None:
                    reference = subject.reference.split("Group/", 2)
                    try:
                        imis_policy.family = Family.objects.filter(uuid=reference[1]).first()
                    except:
                        cls.valid_condition(True, _('Missing  `Family head provided does not exist` attribute'), errors)
        else:
            cls.valid_condition(not fhir_contract.subject, _('Missing  `subject` attribute'), errors)

    @classmethod
    def build_imis_signer(cls, fhir_contract, imis_policy, errors):
        if fhir_contract.signer:
            for signer in  fhir_contract.signer:
                if signer.type:
                    if signer.type.text and signer.party.reference is not None:
                        if signer.type.text == 'HeadOfFamily':
                            reference = signer.party.reference.split("/", 2)
                            try:
                                insuree = Insuree.objects.get(uuid=reference[1])
                                if insuree.head:
                                    imis_policy.family= Family.objects.filter(head_insuree=insuree).first()
                                else:
                                    cls.valid_condition(True, _('Missing  `Member details provided belong to a depedant` attribute'),errors)
                            except:
                                cls.valid_condition(True, _('Missing  `Family head provided does not exist` attribute'),errors)
                        elif signer.type.text == 'EnrolmentOfficer':
                            reference = signer.party.reference.split("/", 2)
                            imis_policy.officer = Officer.objects.get(uuid=reference[1])
                        else:
                            pass
                else:
                    cls.valid_condition(signer.type is None, _('Missing  `type` attribute'),errors)
        else:
            cls.valid_condition(not fhir_contract.signer, _('Missing  `signer` attribute'),errors)

    @classmethod
    def build_imis_insurees(cls,fhir_contract,imis_policy,errors):
        if fhir_contract.term:
            insurees =[]
            for term in  fhir_contract.term:
                if term.asset:
                    for asset in term.asset:
                        if asset.typeReference:
                            for item in asset.typeReference:
                               if item.reference is not None:
                                   reference = item.reference.split("Patient/", 2)
                                   obj = Insuree.objects.get(uuid=reference[1])
                                   if imis_policy.family_id is not None:
                                       if obj.family == imis_policy.family:
                                           if type(insurees) is not list:
                                               insurees = [obj.uuid]
                                           else:
                                               insurees.append(obj.uuid)
                                       else:
                                            if 'Missing  `Invalid Context reference` attribute' not in errors:
                                                cls.valid_condition(True, _('Missing  `Invalid Context reference` attribute'),errors)
                            imis_policy.insurees = insurees
                        else:
                            cls.valid_condition(not asset.context, _('Missing  `context` attribute'),errors)
                else:
                    cls.valid_condition(not term.asset, _('Missing  `asset` attribute'),errors)

        else:
            cls.valid_condition(not fhir_contract, _('Missing  `term` attribute'),errors)

    @classmethod
    def build_imis_product(cls,fhir_contract, imis_policy, errors):
        if fhir_contract.term:
            for term in  fhir_contract.term:
                if term.asset:
                    for asset in term.asset:
                        if asset.valuedItem:
                            for item in asset.valuedItem:
                                if item.entityReference is not None:
                                    if item.entityReference.reference is not None:
                                        reference = item.entityReference.reference.split("InsurancePlan/", 2)
                                        imis_policy.product = Product.objects.get(uuid=reference[1])
                                if item.net is not None:
                                    if item.net.value is not None:
                                        imis_policy.value = item.net.value
                        else:
                            cls.valid_condition(not asset.valuedItem, _('Missing  `valuedItem` attribute'), errors)
                else:
                    cls.valid_condition(not term.asset, _('Missing  `asset` attribute'), errors)

        else:
            cls.valid_condition(not fhir_contract, _('Missing  `term` attribute'), errors)

    @classmethod
    def build_imis_state(cls,fhir_contract, imis_policy, errors):
        if fhir_contract.legalState:
            if fhir_contract.legalState.text:
                if fhir_contract.legalState.text == R4CoverageConfig.get_status_offered_code():
                    imis_policy.stage = ContractState.imis_map_stage(R4CoverageConfig.get_status_offered_code(), imis_policy)
                elif fhir_contract.legalState.text == R4CoverageConfig.get_status_renewed_code():
                    imis_policy.stage = ContractState.imis_map_stage(R4CoverageConfig.get_status_renewed_code(), imis_policy)
                else:
                    pass
        else:
            cls.valid_condition(fhir_contract.legalState is None, _('Missing  `legalState` attribute'), errors)

    @classmethod
    def build_imis_contributions(cls, fhir_contract, imis_policy, errors):
        premiums = []
        if fhir_contract.term:
            for term in fhir_contract.term:
                if term.asset:
                    for asset in term.asset:
                        if asset.extension and len(asset.extension) > 0:
                            if len(asset.extension[0].extension) > 0:
                                imis_contribution = Premium()
                                imis_contribution.uuid = None
                                contribution_extensions = asset.extension[0].extension
                                for fhir_contribution in contribution_extensions:
                                    cls.build_imis_contribution(fhir_contribution, imis_contribution)
                                premiums.append(imis_contribution)
        imis_policy.contributions = premiums

    @classmethod
    def build_imis_contribution(cls, fhir_contribution, imis_contribution):
        if fhir_contribution.url == "payer":
            cls.build_imis_contribution_payer(fhir_contribution, imis_contribution)
        if fhir_contribution.url == "amount":
            cls.build_imis_contribution_amount(fhir_contribution, imis_contribution)
        if fhir_contribution.url == "receipt":
            cls.build_imis_contribution_receipt(fhir_contribution, imis_contribution)
        if fhir_contribution.url == "date":
            cls.build_imis_contribution_pay_date(fhir_contribution, imis_contribution)
        if fhir_contribution.url == "type":
            cls.build_imis_contribution_pay_type(fhir_contribution, imis_contribution)

    @classmethod
    def build_imis_contribution_payer(cls, fhir_contribution, imis_contribution):
        # TODO add payer to contribution
        pass

    @classmethod
    def build_imis_contribution_amount(cls, fhir_contribution, imis_contribution):
        imis_contribution.amount = fhir_contribution.valueMoney.value

    @classmethod
    def build_imis_contribution_receipt(cls, fhir_contribution, imis_contribution):
        imis_contribution.receipt = fhir_contribution.valueString

    @classmethod
    def build_imis_contribution_pay_date(cls, fhir_contribution, imis_contribution):
        imis_contribution.pay_date = fhir_contribution.valueDate

    @classmethod
    def build_imis_contribution_pay_type(cls, fhir_contribution, imis_contribution):
        coding = fhir_contribution.valueCodeableConcept.coding
        if len(coding) > 0:
            code = coding[0]
            imis_contribution.pay_type = code.code
