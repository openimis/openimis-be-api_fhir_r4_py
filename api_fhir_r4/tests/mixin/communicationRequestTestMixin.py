from core import datetime
from claim.models import Claim, ClaimItem, ClaimService

from insuree.test_helpers import create_test_insuree
from location.models import HealthFacility
from medical.test_helpers import create_test_item, create_test_service
from api_fhir_r4.configurations import R4CommunicationRequestConfig as Config
from api_fhir_r4.tests import GenericTestMixin, LocationTestMixin
from api_fhir_r4.utils import TimeUtils
from claim.test_helpers import create_test_claim_context
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
        service_props = {
            'status': self._TEST_SERVICE_STATUS,
            'qty_approved': self._TEST_SERVICE_QUANTITY,
            'qty_provided': self._TEST_SERVICE_QUANTITY,
            'rejection_reason': self._TEST_SERVICE_REJECTED_REASON,
            'availability': self._TEST_ITEM_AVAILABILITY,
            'price_asked': self._TEST_SERVICE_PRICE,
            'price_approved': self._TEST_SERVICE_PRICE,
            'audit_user_id': self._ADMIN_AUDIT_USER_ID,
        }
        item_props = {
            'status': self._TEST_ITEM_STATUS,
            'qty_approved': self._TEST_ITEM_QUANTITY,
            'qty_provided': self._TEST_ITEM_QUANTITY,
            'rejection_reason': self._TEST_ITEM_REJECTED_REASON,
            'availability': self._TEST_ITEM_AVAILABILITY,
            'price_asked': self._TEST_ITEM_PRICE,
            'price_approved': self._TEST_ITEM_PRICE,
            'audit_user_id': self._ADMIN_AUDIT_USER_ID,
        }
        
        
        self.test_claim, self.test_insuree, policy, self.test_hf = create_test_claim_context(
            claim={
                'visit_type': self._TEST_VISIT_TYPE,
                'status': self._TEST_STATUS,
                'feedback_status': Claim.FEEDBACK_SELECTED
                }, 
            claim_admin={
                'uuid': self._TEST_CLAIM_ADMIN_UUID,
            },
            insuree={'uuid': self._TEST_INSUREE_UUID}, 
            product={}, 
            hf={
                'uuid': self._TEST_HF_UUID,
                'name': self._TEST_HF_NAME,
                'level': self._TEST_HF_LEVEL,
                'legal_form_id': self._TEST_HF_LEGAL_FORM,
                'address': self._TEST_ADDRESS,
                'phone': self._TEST_PHONE,
                'fax': self._TEST_FAX,
                'email': self._TEST_EMAIL,
            }, 
            items=[
                item_props
                ], 
            services=[
                service_props
            ])        
 


        self.sub_str[self._TEST_HF_UUID]=self.test_hf.uuid
        self.sub_str[self._TEST_CLAIM_ADMIN_UUID]=self.test_claim.admin.uuid
        self.sub_str[self._TEST_INSUREE_UUID]=self.test_insuree.uuid
        self.sub_str[self._TEST_UUID]=self.test_claim.uuid
        self.sub_str[self._TEST_SERVICE_UUID]=self.test_claim.services.first().service.uuid
        self.sub_str[self._TEST_ITEM_UUID]=self.test_claim.items.first().item.uuid

   

    def create_test_imis_instance(self):
        
        return self.test_claim

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual("active", fhir_obj.status)
        self.assertEqual(f"{Claim.FEEDBACK_SELECTED}", fhir_obj.statusReason.coding[0].code)
        self.assertIn(str(self.test_insuree.uuid), fhir_obj.subject.reference)
        self.assertIn(str(self.test_claim.admin.uuid), fhir_obj.recipient[0].reference)
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
