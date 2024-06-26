from claim.models import Claim, ClaimItem, ClaimService
from insuree.test_helpers import create_test_insuree
from medical.models import Diagnosis

from api_fhir_r4.configurations import R4IdentifierConfig, R4ClaimConfig
from api_fhir_r4.converters import PatientConverter, HealthFacilityOrganisationConverter, \
    ClaimAdminPractitionerConverter, ReferenceConverterMixin
from api_fhir_r4.converters.claimConverter import ClaimConverter
from api_fhir_r4.mapping.claimMapping import ClaimVisitTypeMapping
from api_fhir_r4.models import ClaimV2 as FHIRClaim
from fhir.resources.R4B.period import Period
from fhir.resources.R4B.money import Money
from location.models import HealthFacility
from location.test_helpers import create_test_village, create_test_health_facility
from medical.models import Item, Service
from medical.test_helpers import create_test_item, create_test_service
from claim.test_helpers import create_test_claimservice,create_test_claimitem,create_test_claim_admin
from api_fhir_r4.tests import GenericTestMixin
from api_fhir_r4.utils import TimeUtils


class ClaimTestMixin(GenericTestMixin):
    _TEST_UUID = "315c3b16-62eb-11ea-8e75-df3492b349f6"
    _TEST_CLAIM_CODE = 'T00001'
    _TEST_DATE_FROM = TimeUtils.str_to_date('2021-02-03')
    _TEST_DATE_TO = TimeUtils.str_to_date('2021-02-03')

    # diagnosis data
    _TEST_MAIN_ICD_CODE = 'T_CD'
    _TEST_MAIN_ICD_NAME = 'Test diagnosis'

    _TEST_CLAIMED = 21100
    _TEST_DATE_CLAIMED = '2021-02-03T00:00:00'
    _TEST_GUARANTEE_ID = "guarantee_id"
    _TEST_EXPLANATION = "example explanation"
    _TEST_VISIT_TYPE = "O"
    _TEST_STATUS = Claim.STATUS_REJECTED

    # claim item data
    _TEST_ITEM_CODE = "0004"
    _TEST_ITEM_UUID = "e2bc1546-390b-4d41-8571-632ecf7a0936"
    _TEST_ITEM_QUANTITY_PROVIDED = 10.0
    _TEST_ITEM_PRICE_ASKED = 10.0
    _TEST_ITEM_EXPLANATION = "item_explanation"
    _TEST_ITEM_TYPE = 'D'

    # claim service data
    _TEST_SERVICE_CODE = "M7"
    _TEST_SERVICE_UUID = "a17602f4-e9ff-4f42-a6a4-ccefcb23b4d6"
    _TEST_SERVICE_QUANTITY_PROVIDED = 1
    _TEST_SERVICE_PRICE_ASKED = 21000.0
    _TEST_SERVICE_EXPLANATION = "service_explanation"
    _TEST_SERVICE_TYPE = 'D'

    # hf test data
    _TEST_HF_ID = 10000
    _TEST_HF_UUID = "6d0eea8c-62eb-11ea-94d6-c36229a16c2f"
    _TEST_HF_CODE = "12345678"
    _TEST_HF_NAME = "TEST_NAME"
    _TEST_HF_LEVEL = "H"
    _TEST_HF_LEGAL_FORM = "G"
    _TEST_ADDRESS = "TEST_ADDRESS"
    _TEST_PHONE = "133-996-476"
    _TEST_FAX = "1-408-999 8888"
    _TEST_EMAIL = "TEST@TEST.com"

    # insuree and claim admin data
    _TEST_INSUREE_UUID = "76aca309-f8cf-4890-8f2e-b416d78de00b"
    _TEST_CLAIM_ADMIN_UUID = "044c33d1-dbf3-4d6a-9924-3797b461e535"

    _ADMIN_AUDIT_USER_ID = -1
    test_insuree = None
    test_icd = None
    test_hf = None
    test_claim_admin = None
    test_claim = None
    test_claim_item = None
    test_claim_service = None
    sub_str = {}

    def setUp(self):
        super(ClaimTestMixin, self).setUp()
        self.test_icd = Diagnosis()
        self.test_icd.code = self._TEST_MAIN_ICD_CODE
        self.test_icd.name = self._TEST_MAIN_ICD_NAME
        self.test_icd.audit_user_id = self._ADMIN_AUDIT_USER_ID
        self.test_icd.save()

        self.test_claim_admin= create_test_claim_admin()
        self.test_insuree = create_test_insuree()

        self.create_test_hf()

        self.test_claim=self.create_test_claim()
        self.test_claim_item= self.create_test_claim_item()
        self.test_claim_service = self.create_test_claim_service()
        self.sub_str[self._TEST_HF_UUID]=self.test_hf.uuid
        self.sub_str[self._TEST_CLAIM_ADMIN_UUID]=self.test_claim_admin.uuid
        self.sub_str[self._TEST_INSUREE_UUID]=self.test_insuree.uuid
        self.sub_str[self._TEST_SERVICE_UUID]=self.test_claim_service.service.uuid
        self.sub_str[self._TEST_ITEM_UUID]=self.test_claim_item.item.uuid
        self.sub_str[self._TEST_SERVICE_CODE]=self.test_claim_service.service.code
        self.sub_str[self._TEST_ITEM_CODE]=self.test_claim_item.item.code
        self.sub_str[self._TEST_UUID]=self.test_claim.uuid
        self._TEST_HF_ID = self.test_hf.id
        self._TEST_HF_UUID = self.test_hf.uuid
        
    def create_test_hf(self):
        self.test_hf = create_test_health_facility(
            self._TEST_HF_CODE,
            self.test_insuree.family.location.parent.parent.id,
            custom_props = {
                'name': self._TEST_HF_NAME,
                'level':self._TEST_HF_LEVEL,
                'legal_form_id':self._TEST_HF_LEGAL_FORM,
                'address':self._TEST_ADDRESS,
                'phone':self._TEST_PHONE,
                'fax':self._TEST_FAX,
                'email':self._TEST_EMAIL,
            }
        )
        return self.test_hf
    def create_test_claim(self):
        imis_claim = Claim()
        imis_claim.uuid = self._TEST_UUID
        imis_claim.insuree = self.test_insuree
        imis_claim.code = self._TEST_CLAIM_CODE
        imis_claim.date_from = TimeUtils.str_to_date(self._TEST_DATE_FROM)
        imis_claim.date_to = TimeUtils.str_to_date(self._TEST_DATE_TO)

        imis_claim.icd = self.test_icd

        imis_claim.claimed = self._TEST_CLAIMED
        imis_claim.date_claimed = TimeUtils.str_to_date(self._TEST_DATE_CLAIMED)
        imis_claim.health_facility = self.test_hf
        imis_claim.guarantee_id = self._TEST_GUARANTEE_ID
        imis_claim.admin = self.test_claim_admin
        imis_claim.visit_type = self._TEST_VISIT_TYPE
        imis_claim.status = self._TEST_STATUS
        imis_claim.audit_user_id = self._ADMIN_AUDIT_USER_ID
        imis_claim.save()
        return imis_claim
    
    def create_test_claim_item(self):
        item = Item.objects.filter(code=self._TEST_ITEM_CODE).first()
        if item is None:
            item = create_test_item(
                self._TEST_ITEM_TYPE,
                custom_props={"code": self._TEST_ITEM_CODE}
            )
        return create_test_claimitem( self.test_claim, self._TEST_ITEM_TYPE,
            custom_props={
                "item": item,
                "price_asked": self._TEST_ITEM_PRICE_ASKED,
                "qty_provided": self._TEST_ITEM_QUANTITY_PROVIDED,
                "explanation": self._TEST_ITEM_EXPLANATION,
                "audit_user_id": self._ADMIN_AUDIT_USER_ID
            }
        )
    
        
    def create_test_claim_service(self):
        service = Service.objects.filter(code=self._TEST_ITEM_CODE).first()
        if service is None:
            service = create_test_service( 
                self._TEST_SERVICE_TYPE,
                custom_props={"code": self._TEST_ITEM_CODE}
            )
        return create_test_claimservice(self.test_claim, self._TEST_SERVICE_TYPE,
            custom_props={
                "service": service,
                "price_asked": self._TEST_SERVICE_PRICE_ASKED,
                "qty_provided": self._TEST_SERVICE_QUANTITY_PROVIDED,
                "explanation": self._TEST_SERVICE_EXPLANATION,
                "audit_user_id": self._ADMIN_AUDIT_USER_ID
            }
        )

    def create_test_imis_instance(self):
        return self.test_claim

    def verify_imis_instance(self, imis_obj):
        self.assertIsNotNone(imis_obj.insuree)
        self.assertEqual(self._TEST_CLAIM_CODE, imis_obj.code)
        self.assertEqual(self._TEST_DATE_FROM.isoformat(), imis_obj.date_from.isoformat())
        self.assertEqual(self._TEST_DATE_TO.isoformat(), imis_obj.date_to.isoformat())
        self.assertEqual(self._TEST_MAIN_ICD_CODE, imis_obj.icd.code)
        self.assertEqual(self._TEST_CLAIMED, imis_obj.claimed)
        self.assertEqual(self._TEST_DATE_CLAIMED, imis_obj.date_claimed.isoformat())
        self.assertIsNotNone(imis_obj.health_facility)
        self.assertEqual(self._TEST_GUARANTEE_ID, imis_obj.guarantee_id)
        self.assertEqual(self._TEST_EXPLANATION, imis_obj.explanation)
        self.assertIsNotNone(imis_obj.admin)
        self.assertEqual(self._TEST_VISIT_TYPE, imis_obj.visit_type)

        self.assertEqual(self.test_claim_item.item.code, imis_obj.submit_items[0].item.code)
        #FIXME self.assertEqual(self._TEST_ITEM_QUANTITY_PROVIDED, imis_obj.submit_items[0].qty_provided)
        #self.assertEqual(self._TEST_ITEM_PRICE_ASKED, imis_obj.submit_items[0].price_asked)

        self.assertEqual(self.test_claim_service.service.code, imis_obj.submit_services[0].service.code)
        #self.assertEqual(self._TEST_SERVICE_QUANTITY_PROVIDED, imis_obj.submit_services[0].qty_provided)
        #self.assertEqual(self._TEST_SERVICE_PRICE_ASKED, imis_obj.submit_services[0].price_asked)

    def create_test_fhir_instance(self):
        fhir_claim = {}
        fhir_claim["use"] = 'claim'
        fhir_claim["status"] = 'active'
        fhir_claim["created"] = self._TEST_DATE_CLAIMED
        fhir_claim = FHIRClaim(**fhir_claim)

        mapping = ClaimVisitTypeMapping.fhir_claim_visit_type_coding[self._TEST_VISIT_TYPE]
        fhir_claim.type = ClaimConverter.build_codeable_concept_from_coding(
            ClaimConverter.build_fhir_mapped_coding(mapping))

        fhir_claim.patient = PatientConverter.build_fhir_resource_reference(self.test_insuree)
        claim_code = ClaimConverter.build_fhir_identifier(
            self._TEST_CLAIM_CODE,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_claim_code_type()
        )
        fhir_claim.identifier = [claim_code]

        billable_period = Period.construct()
        billable_period.start = self._TEST_DATE_FROM
        billable_period.end = self._TEST_DATE_TO
        fhir_claim.billablePeriod = billable_period

        diagnoses = []
        ClaimConverter.build_fhir_diagnosis(
            diagnoses,
            self.test_icd,
        )
        fhir_claim.diagnosis = diagnoses

        supportingInfo = []
        guarantee_id_code = R4ClaimConfig.get_fhir_claim_information_guarantee_id_code()
        ClaimConverter.build_fhir_string_information(supportingInfo, guarantee_id_code, self._TEST_GUARANTEE_ID)
        explanation_code = R4ClaimConfig.get_fhir_claim_information_explanation_code()
        ClaimConverter.build_fhir_string_information(supportingInfo, explanation_code, self._TEST_EXPLANATION)

        fhir_claim.supportingInfo = supportingInfo

        fhir_claim.enterer = ClaimAdminPractitionerConverter.build_fhir_resource_reference(
            self.test_claim_admin
        )

        fhir_claim.item = []
        type = R4ClaimConfig.get_fhir_claim_item_code()
        ClaimConverter.build_fhir_item(fhir_claim, self._TEST_ITEM_CODE, type, self.test_claim_item,
                                       reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE)
        type = R4ClaimConfig.get_fhir_claim_service_code()
        ClaimConverter.build_fhir_item(fhir_claim, self._TEST_SERVICE_CODE, type, self.test_claim_service,
                                       reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE)

        fhir_claim.provider = HealthFacilityOrganisationConverter.build_fhir_resource_reference(
            self.test_hf,
            display=self._TEST_HF_CODE
        )

        total = Money.construct()
        total.value = self._TEST_CLAIMED
        fhir_claim.total = total

        return fhir_claim

    def verify_fhir_instance(self, fhir_obj):
        self.assertIsNotNone(fhir_obj.patient.reference)
        for identifier in fhir_obj.identifier:
            if identifier.type.coding[0].code == R4IdentifierConfig.get_fhir_claim_code_type():
                self.assertEqual(self._TEST_CLAIM_CODE, identifier.value)

        self.assertIn(fhir_obj.billablePeriod.start.isoformat(), self._TEST_DATE_FROM.isoformat())
        self.assertIn(fhir_obj.billablePeriod.end.isoformat(), self._TEST_DATE_TO.isoformat())
        for diagnosis in fhir_obj.diagnosis:
            code = diagnosis.diagnosisCodeableConcept.coding[0].code
            self.assertEqual(self._TEST_MAIN_ICD_CODE, code)

        self.assertEqual(self._TEST_CLAIMED, fhir_obj.total.value)
        self.assertIn(fhir_obj.created.isoformat(), self._TEST_DATE_CLAIMED)
        for supportingInfo in fhir_obj.supportingInfo:
            if supportingInfo.category.text == R4ClaimConfig.get_fhir_claim_information_explanation_code():
                self.assertEqual(self._TEST_EXPLANATION, supportingInfo.valueString)
            elif supportingInfo.category.text == R4ClaimConfig.get_fhir_claim_information_guarantee_id_code():
                self.assertEqual(self._TEST_GUARANTEE_ID, supportingInfo.valueString)
        self.assertIsNotNone(fhir_obj.provider.reference)
        self.assertIn(str(self.test_hf.uuid), fhir_obj.provider.reference)
        self.assertIsNotNone(fhir_obj.enterer.reference)
        self.assertIn(str(self.test_claim_admin.uuid), fhir_obj.enterer.reference)
        self.assertIsNotNone(fhir_obj.patient.reference)
        self.assertIn(str(self.test_insuree.uuid), fhir_obj.patient.reference)
        for item in fhir_obj.item:
            if item.category.text == R4ClaimConfig.get_fhir_claim_item_code():
                self.assertEqual(self.test_claim_item.item.code, item.productOrService.text)
                self.assertEqual(self._TEST_ITEM_QUANTITY_PROVIDED, item.quantity.value)
                self.assertEqual(self._TEST_ITEM_PRICE_ASKED, item.unitPrice.value)
            elif item.category.text == R4ClaimConfig.get_fhir_claim_service_code():
                return None#FIXME
                self.assertEqual(self.test_claim_service.service.code, item.productOrService.text)
                self.assertEqual(self._TEST_SERVICE_QUANTITY_PROVIDED, item.quantity.value)
                self.assertEqual(self._TEST_SERVICE_PRICE_ASKED, item.unitPrice.value)
