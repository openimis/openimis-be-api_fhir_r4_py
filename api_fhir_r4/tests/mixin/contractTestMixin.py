import core
import uuid

from policy.models import Policy
from insuree.models import InsureePolicy

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig, R4CoverageConfig
from api_fhir_r4.converters import ContractConverter
from api_fhir_r4.tests import GenericTestMixin

from django.utils.translation import gettext as _
from fhir.resources.R4B.contract import Contract, ContractTerm, ContractTermOffer, \
    ContractTermAsset, ContractTermOfferParty, ContractTermAssetValuedItem
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.money import Money
from fhir.resources.R4B.period import Period
from fhir.resources.R4B.reference import Reference
from api_fhir_r4.utils import TimeUtils

from core.test_helpers import create_test_officer
from insuree.test_helpers import create_test_insuree
from product.test_helpers import create_test_product


class ContractTestMixin(GenericTestMixin):

    _TEST_POLICY_ID = "100000"
    _TEST_POLICY_ENROLL_DATE = "2021-06-20T00:00:00"
    _TEST_POLICY_START_DATE = "2021-06-20T00:00:00"
    _TEST_POLICY_EFFECTIVE_DATE = "2021-06-20T00:00:00"
    _TEST_POLICY_EXPIRED_DATE = "2022-06-19T00:00:00"
    _TEST_POLICY_STATUS = 1
    _TEST_POLICY_STAGE = 'N'
    _TEST_GROUP_UUID = "e8bbb7e4-19ef-4bef-9342-9ab6b9a928d3"
    _TEST_OFFICER_UUID = "ff7db42d-874b-400a-bba7-e59b273ae123"
    _TEST_INSUREE_UUID = "f8c56ada-d76d-4f6c-aad3-cfddc9fb38eb"
    _TEST_PRODUCT_CODE = "TE123"
    _TEST_PRODUCT_UUID = "8ed8d2d9-2644-4d29-ba37-ab772386cfca"

    _TEST_POLICY_VALUE = 10000.0

    def create_test_imis_instance(self):
        imis_policy = Policy()
        imis_policy.id = self._TEST_POLICY_ID

        # create mocked insuree
        imis_insuree = create_test_insuree(with_family=True)
        imis_insuree.uuid = self._TEST_INSUREE_UUID
        imis_insuree.save()

        # update family uuid
        imis_family = imis_insuree.family
        imis_family.uuid = self._TEST_GROUP_UUID
        imis_family.save()

        # create mocked product
        imis_product = create_test_product(self._TEST_PRODUCT_CODE, valid=True, custom_props={})
        imis_product.uuid = self._TEST_PRODUCT_UUID
        imis_product.save()

        imis_policy.family = imis_family
        imis_policy.product = imis_product

        imis_policy.enroll_date = TimeUtils.str_to_date(self._TEST_POLICY_ENROLL_DATE)
        imis_policy.start_date = TimeUtils.str_to_date(self._TEST_POLICY_START_DATE)
        imis_policy.effective_date = TimeUtils.str_to_date(self._TEST_POLICY_EFFECTIVE_DATE)
        imis_policy.expiry_date = TimeUtils.str_to_date(self._TEST_POLICY_EXPIRED_DATE)

        imis_policy.stage = self._TEST_POLICY_STAGE
        imis_policy.status = self._TEST_POLICY_STATUS
        imis_policy.value = self._TEST_POLICY_VALUE
        imis_policy.audit_user_id = -1

        # create mocked officer
        imis_officer = create_test_officer()
        imis_officer.uuid = self._TEST_OFFICER_UUID
        imis_officer.save()
        imis_policy.officer = imis_officer

        # save mock policy
        imis_policy.save()

        # create mock policy insuree
        imis_policy_insuree = InsureePolicy(
            policy=imis_policy,
            insuree=imis_insuree,
            audit_user_id=-1
        )
        imis_policy_insuree.save()

        return imis_policy

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_POLICY_ENROLL_DATE, imis_obj.enroll_date.isoformat())
        self.assertEqual(self._TEST_POLICY_START_DATE, imis_obj.start_date.isoformat())
        self.assertEqual(self._TEST_POLICY_EFFECTIVE_DATE, imis_obj.effective_date.isoformat())
        self.assertEqual(self._TEST_POLICY_EXPIRED_DATE, imis_obj.expiry_date.isoformat())
        self.assertEqual(self._TEST_GROUP_UUID, str(uuid.UUID(imis_obj.family.uuid)))
        self.assertEqual(self._TEST_OFFICER_UUID, str(uuid.UUID(imis_obj.officer.uuid)))
        self.assertEqual(self._TEST_PRODUCT_CODE, imis_obj.product.code)
        self.assertEqual(self._TEST_PRODUCT_UUID, str(uuid.UUID(imis_obj.product.uuid)))

    def create_test_fhir_instance(self):
        # create some dependency
        # create mocked insuree
        imis_insuree = create_test_insuree(with_family=True)
        imis_insuree.uuid = self._TEST_INSUREE_UUID
        imis_insuree.save()

        # create mocked family
        imis_family = imis_insuree.family
        imis_family.uuid = self._TEST_GROUP_UUID
        imis_family.save()

        # create mocked product
        imis_product = create_test_product(self._TEST_PRODUCT_CODE, valid=True, custom_props={})
        imis_product.uuid = self._TEST_PRODUCT_UUID
        imis_product.save()

        # create mocked officer
        imis_officer = create_test_officer()
        imis_officer.uuid = self._TEST_OFFICER_UUID
        imis_officer.save()

        if hasattr(core, 'currency'):
            currency = core.currency
        else:
            currency = "EUR"

        fhir_contract = Contract.construct()
        id = ContractConverter.build_fhir_identifier(
            self._TEST_POLICY_ID,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_id_type_code()
        )
        identifiers = [id]
        fhir_contract.identifier = identifiers

        author = Reference.construct()
        author.reference = f"Practitioner/{self._TEST_OFFICER_UUID}"
        fhir_contract.author = author

        subject = Reference.construct()
        subject.reference = f"Group/{self._TEST_GROUP_UUID}"
        fhir_contract.subject = [subject]

        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/contract-scope"
        fhir_contract.scope = ContractConverter.build_codeable_concept(code="informal", system=system)
        if len(fhir_contract.scope.coding) == 1:
            fhir_contract.scope.coding[0].display = _("Informal Sector")

        # contract term build
        contract_term = ContractTerm.construct()

        # contract term offer
        offer = ContractTermOffer.construct()
        offer_party = ContractTermOfferParty.construct()
        reference = Reference.construct()
        insuree_uuid = self._TEST_INSUREE_UUID
        reference.reference = f"Patient/{insuree_uuid}"
        offer_party.reference = [reference]
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/contract-resource-party-role"
        offer_party.role = ContractConverter.build_codeable_concept(code="beneficiary", system=system)
        if len(offer_party.role.coding) == 1:
            offer_party.role.coding[0].display = _("Beneficiary")

        offer.party = [offer_party]
        contract_term.offer = offer

        contract_term_asset = ContractTermAsset.construct()
        # contract term asset extensions - premium

        typeReference = Reference.construct()
        typeReference.reference = f"Patient/{insuree_uuid}"
        contract_term_asset.typeReference = [typeReference]

        valued_item = ContractTermAssetValuedItem.construct()
        typeReference = Reference.construct()
        typeReference.reference = f"InsurancePlan/{self._TEST_PRODUCT_UUID}"
        valued_item.entityReference = typeReference
        policy_value = Money.construct()
        policy_value.value = self._TEST_POLICY_VALUE
        valued_item.net = policy_value
        contract_term_asset.valuedItem = [valued_item]

        period_use = Period.construct()
        period = Period.construct()
        #if imis_policy.effective_date is not None:
        period_use.start = self._TEST_POLICY_EFFECTIVE_DATE
        #if period_use.start is None:
        period.start = period_use.start
        #if imis_policy.expiry_date is not None:
        period_use.end = self._TEST_POLICY_EXPIRED_DATE
        period.end = period_use.end

        contract_term_asset.usePeriod = [period_use]
        contract_term_asset.period = [period]

        contract_term.asset = [contract_term_asset]
        fhir_contract.term = [contract_term]

        fhir_contract.status = R4CoverageConfig.get_status_offered_code()
        fhir_contract.legalState = ContractConverter.build_simple_codeable_concept(
            R4CoverageConfig.get_status_offered_code()
        )
        return fhir_contract

    def verify_fhir_instance(self, fhir_obj):
        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = ContractConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_id_type_code():
                self.assertEqual(self._TEST_POLICY_ID, identifier.value)
        self.assertIn(f"Group/{self._TEST_GROUP_UUID}", fhir_obj.subject[0].reference)
        self.assertIn(f"Practitioner/{self._TEST_OFFICER_UUID}", fhir_obj.author.reference)
        self.assertEqual("Offered", fhir_obj.status)
        self.assertEqual("Offered", fhir_obj.legalState.text)
        term = fhir_obj.term[0]
        offer = term.offer
        asset = term.asset[0]
        reference_asset = asset.typeReference[0].reference
        reference_asset = reference_asset.split('Patient/')[1].lower()
        self.assertEqual(self._TEST_INSUREE_UUID, reference_asset)
        period = asset.period[0]
        self.assertEqual(self._TEST_POLICY_START_DATE, period.start.isoformat()+"T00:00:00")
        self.assertEqual(self._TEST_POLICY_EXPIRED_DATE, period.end.isoformat()+"T00:00:00")
        use_period = asset.usePeriod[0]
        self.assertEqual(self._TEST_POLICY_EFFECTIVE_DATE, use_period.start.isoformat()+"T00:00:00")
        self.assertEqual(self._TEST_POLICY_EXPIRED_DATE, use_period.end.isoformat()+"T00:00:00")
        valued_item = asset.valuedItem[0]
        self.assertIn(f"InsurancePlan/{self._TEST_PRODUCT_UUID}", valued_item.entityReference.reference)
        self.assertEqual(self._TEST_POLICY_VALUE, valued_item.net.value)
