from core import datetime
from claim.models import Claim, ClaimItem, ClaimService

from insuree.test_helpers import create_test_insuree
from location.models import HealthFacility
from medical.test_helpers import create_test_item, create_test_service
from api_fhir_r4.configurations import R4CommunicationRequestConfig as Config
from api_fhir_r4.tests import GenericTestMixin, LocationTestMixin
from api_fhir_r4.utils import TimeUtils
from claim.test_helpers import create_test_claim_admin
from location.test_helpers import create_test_village, create_test_health_facility
from medical.models import Diagnosis


class CommunicationRequestTestMixin(GenericTestMixin):
    _TEST_CODE = 'codeTest'
    _TEST_UUID = "7ac646cb-d3cd-4660-baeb-ee34ecf0354e"
    _TEST_STATUS = Claim.STATUS_ENTERED
    _TEST_STATUS_DISPLAY = "entered"
    _TEST_OUTCOME = "queued"
    _TEST_ADJUSTMENT = "adjustment"
    _TEST_DATE_PROCESSED = "2010-11-16T00:00:00"
    _TEST_APPROVED = 1000.00
    _TEST_REJECTION_REASON = 0
    _TEST_VISIT_TYPE = "O"

    # claim item data
    _TEST_ITEM_CODE = "iCode"
    _TEST_ITEM_UUID = "e2bc1546-390b-4d41-8571-632ecf7a0936"
    _TEST_ITEM_STATUS = Claim.STATUS_ENTERED
    _TEST_ITEM_QUANTITY = 20
    _TEST_ITEM_PRICE = 10.0
    _TEST_ITEM_REJECTED_REASON = 0

    # claim service data
    _TEST_SERVICE_CODE = "sCode"
    _TEST_SERVICE_UUID = "a17602f4-e9ff-4f42-a6a4-ccefcb23b4d6"
    _TEST_SERVICE_STATUS = Claim.STATUS_ENTERED
    _TEST_SERVICE_QUANTITY = 1
    _TEST_SERVICE_PRICE = 800
    _TEST_SERVICE_REJECTED_REASON = 0

    _TEST_ID = 9999
    _PRICE_ASKED = 1000
    _PRICE_APPROVED = 1000
    _ADMIN_AUDIT_USER_ID = 1

    _TEST_ITEM_AVAILABILITY = True

    _TEST_ITEM_TYPE = 'D'
    _TEST_SERVICE_TYPE = 'D'

    # insuree and claim admin data
    _TEST_INSUREE_UUID = "76aca309-f8cf-4890-8f2e-b416d78de00b"
    _TEST_CLAIM_ADMIN_UUID = "044c33d1-dbf3-4d6a-9924-3797b461e535"

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
    test_claim_admin = None
    test_insuree = None
    test_claim = None
    test_hf = None
    test_village = None
    sub_str = {}
    def setUp(self):
        super(CommunicationRequestTestMixin, self).setUp()
        self.test_insuree = create_test_insuree()
        self.test_village = self.test_insuree.family.location
        self.test_hf = self._create_test_health_facility()
        self._TEST_HF_ID = self.test_hf.id
        self.test_claim_admin = create_test_claim_admin( custom_props={'health_facility_id': self.test_hf.id})
        self.test_claim = self.create_test_imis_instance()
        self.test_claim_item = self.create_test_claim_item()
        self.test_claim_service = self.create_test_claim_service()
        
        self.sub_str[self._TEST_HF_UUID]=self.test_hf.uuid
        self.sub_str[self._TEST_CLAIM_ADMIN_UUID]=self.test_claim_admin.uuid
        self.sub_str[self._TEST_INSUREE_UUID]=self.test_insuree.uuid
        self.sub_str[self._TEST_UUID]=self.test_claim.uuid
        self.sub_str[self._TEST_SERVICE_UUID]=self.test_claim_service.service.uuid
        self.sub_str[self._TEST_ITEM_UUID]=self.test_claim_item.item.uuid

    def create_test_claim_item(self):
        item = ClaimItem()
        item.item = create_test_item(
            self._TEST_ITEM_TYPE,
            custom_props={"code": self._TEST_ITEM_CODE}
        )
        item.claim = self.test_claim
        item.status = self._TEST_ITEM_STATUS
        item.qty_approved = self._TEST_ITEM_QUANTITY
        item.qty_provided = self._TEST_ITEM_QUANTITY
        item.rejection_reason = self._TEST_ITEM_REJECTED_REASON
        item.availability = self._TEST_ITEM_AVAILABILITY
        item.price_asked = self._TEST_ITEM_PRICE
        item.price_approved = self._TEST_ITEM_PRICE
        item.audit_user_id = self._ADMIN_AUDIT_USER_ID
        item.save()
        return item

    def create_test_claim_service(self):
        service = ClaimService()
        service.service = create_test_service(
            self._TEST_SERVICE_TYPE,
            custom_props={"code": self._TEST_SERVICE_CODE}
        )
        service.claim = self.test_claim
        service.status = self._TEST_SERVICE_STATUS
        service.qty_approved = self._TEST_SERVICE_QUANTITY
        service.qty_provided = self._TEST_SERVICE_QUANTITY
        service.rejection_reason = self._TEST_SERVICE_REJECTED_REASON
        service.availability = self._TEST_ITEM_AVAILABILITY
        service.price_asked = self._TEST_SERVICE_PRICE
        service.price_approved = self._TEST_SERVICE_PRICE
        service.audit_user_id = self._ADMIN_AUDIT_USER_ID
        service.save()
        return service

    def _create_test_health_facility(self):
        
        hf = create_test_health_facility(
            self._TEST_HF_CODE,
            self.test_village.parent.parent.id,
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
        return hf

    def create_test_imis_instance(self):
        if self.test_claim is None:
            imis_claim = Claim()
            imis_claim.id = self._TEST_ID
            imis_claim.uuid = self._TEST_UUID
            imis_claim.code = self._TEST_CODE
            imis_claim.status = self._TEST_STATUS
            imis_claim.adjustment = self._TEST_ADJUSTMENT
            imis_claim.date_processed = TimeUtils.str_to_date(self._TEST_DATE_PROCESSED)
            imis_claim.approved = self._TEST_APPROVED
            imis_claim.rejection_reason = self._TEST_REJECTION_REASON
            imis_claim.insuree = self.test_insuree 
            
            imis_claim.health_facility = self._create_test_health_facility()
            imis_claim.icd = Diagnosis(code='ICD00I', name='TEST ICD')
            imis_claim.icd.audit_user_id = self._ADMIN_AUDIT_USER_ID
            imis_claim.icd.save()
            imis_claim.audit_user_id = self._ADMIN_AUDIT_USER_ID
            imis_claim.icd.date_from = datetime.date(2018, 12, 12)
            imis_claim.date_from = datetime.date(2018, 12, 12)
            imis_claim.date_claimed = datetime.date(2018, 12, 14)
            imis_claim.visit_type = self._TEST_VISIT_TYPE
            imis_claim.admin =  self.test_claim_admin
            imis_claim.feedback_status = Claim.FEEDBACK_SELECTED
            imis_claim.save()
            self.test_claim = imis_claim
        return self.test_claim

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual("active", fhir_obj.status)
        self.assertEqual(f"{Claim.FEEDBACK_SELECTED}", fhir_obj.statusReason.coding[0].code)
        self.assertIn(str(self.test_insuree.uuid), fhir_obj.subject.reference)
        self.assertIn(str(self.test_claim_admin.uuid), fhir_obj.recipient[0].reference)
        self.assertIn(str(self.test_claim.uuid), fhir_obj.about[0].reference)
        for payload in fhir_obj.payload:
            code = payload.extension[0].valueCodeableConcept.coding[0].code
            content_string = payload.contentString
            if code == Config.get_fhir_care_rendered_code():
                self.assertEqual("Care Rendered? (yes|no)", content_string)
            elif code == Config.get_fhir_payment_asked_code():
                self.assertEqual("Payment Asked? (yes|no)", content_string)
            elif code == Config.get_fhir_drug_prescribed_code():
                self.assertEqual("Drug Prescribed? (yes|no)", content_string)
            elif code == Config.get_fhir_drug_received_code():
                self.assertEqual("Drug Received? (yes|no)", content_string)
            elif code == Config.get_fhir_asessment_code():
                self.assertEqual("Asessment? (0|1|2|3|4|5)", content_string)
