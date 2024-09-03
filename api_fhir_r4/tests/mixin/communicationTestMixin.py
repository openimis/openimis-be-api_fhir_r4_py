from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.converters import CommunicationConverter
from api_fhir_r4.configurations import R4CommunicationRequestConfig as Config
from api_fhir_r4.tests import GenericTestMixin, LocationTestMixin
from api_fhir_r4.utils import TimeUtils
from fhir.resources.R4B.communication import Communication, CommunicationPayload
from fhir.resources.R4B.extension import Extension
from claim.models import Claim, ClaimItem, ClaimService, Feedback
from claim.test_helpers import (
    create_test_claim_admin,
    create_test_claimitem,
    create_test_claimservice,
    create_test_claim_context
)
from core import datetime
from location.models import HealthFacility
from location.test_helpers import create_test_village, create_test_health_facility
from insuree.test_helpers import create_test_insuree
from medical.test_helpers import create_test_item, create_test_service
from medical.models import Diagnosis


class CommunicationTestMixin(GenericTestMixin):
    # feedback expected data
    _TEST_FEE_UUID = "612a1e12-ce44-4632-90a8-129ec714ec59"
    _TEST_CARE_RENDERED = False
    _TEST_PAYMENT_ASKED = True
    _TEST_DRUG_PRESCRIBED = True
    _TEST_DRUG_RECEIVED = False
    _TEST_ASESSMENT = '3'

    # claim data
    _TEST_CLAIM_CODE = 'codeTest'
    _TEST_CLAIM_UUID = "7ac646cb-d3cd-4660-baeb-ee34ecf0354e"
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
    _TEST_INSUREE = None

    def setUp(self):
        super(CommunicationTestMixin, self).setUp()
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
        self._TEST_CLAIM, self.test_insuree, policy, self.test_hf = create_test_claim_context(
            claim={
                'visit_type': self._TEST_VISIT_TYPE,
                'code': self._TEST_CLAIM_CODE,
                'uuid': self._TEST_CLAIM_UUID,
                'status': self._TEST_STATUS,
                }, 
            claim_admin={
                'uuid': self._TEST_CLAIM_ADMIN_UUID,
                'feedback_status': Claim.FEEDBACK_SELECTED
            },
            insuree={'uuid': self._TEST_INSUREE_UUID}, 
            product={}, 
            hf={
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
 

    def create_test_imis_instance(self):
        imis_feedback = Feedback()
        imis_feedback.claim = self._TEST_CLAIM
        imis_feedback.care_rendered = self._TEST_CARE_RENDERED
        imis_feedback.payment_asked = self._TEST_PAYMENT_ASKED
        imis_feedback.drug_prescribed = self._TEST_DRUG_PRESCRIBED
        imis_feedback.drug_received = self._TEST_DRUG_RECEIVED
        imis_feedback.asessment = self._TEST_ASESSMENT
        return imis_feedback

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(imis_obj.claim.uuid.lower(), self._TEST_CLAIM_UUID.lower())
        self.assertEqual(imis_obj.care_rendered, self._TEST_CARE_RENDERED)
        self.assertEqual(imis_obj.payment_asked, self._TEST_PAYMENT_ASKED)
        self.assertEqual(imis_obj.drug_prescribed, self._TEST_DRUG_PRESCRIBED)
        self.assertEqual(imis_obj.asessment, self._TEST_ASESSMENT)

    def create_test_fhir_instance(self):
        fhir_communication = {}
        fhir_communication['status'] = "completed"

        fhir_communication = Communication(**fhir_communication)

        fhir_payload = []
        # care rendered
        payload = {}
        payload['contentString'] = "no"
        payload = CommunicationPayload(**payload)
        payload.extension = []

        extension = Extension.construct()
        url = f'{GeneralConfiguration.get_system_base_url()}StructureDefinition/communication-payload-type'
        system = f'{GeneralConfiguration.get_system_base_url()}CodeSystem/feedback-payload'
        extension.url = url
        extension.valueCodeableConcept = CommunicationConverter.build_codeable_concept(
            system=system,
            code=Config.get_fhir_care_rendered_code()
        )
        payload.extension.append(extension)

        fhir_payload.append(payload)

        # payment asked
        payload = {}
        payload['contentString'] = "yes"
        payload = CommunicationPayload(**payload)
        payload.extension = []

        extension = Extension.construct()
        extension.url = url
        extension.valueCodeableConcept = CommunicationConverter.build_codeable_concept(
            system=system,
            code=Config.get_fhir_payment_asked_code()
        )
        payload.extension.append(extension)

        fhir_payload.append(payload)

        # drug prescribed
        payload = {}
        payload['contentString'] = "yes"
        payload = CommunicationPayload(**payload)
        payload.extension = []

        extension = Extension.construct()
        extension.url = url
        extension.valueCodeableConcept = CommunicationConverter.build_codeable_concept(
            system=system,
            code=Config.get_fhir_drug_prescribed_code()
        )
        payload.extension.append(extension)

        fhir_payload.append(payload)

        # drug received
        payload = {}
        payload['contentString'] = "no"
        payload = CommunicationPayload(**payload)
        payload.extension = []
        extension = Extension.construct()
        extension.url = url
        extension.valueCodeableConcept = CommunicationConverter.build_codeable_concept(
            system=system,
            code=Config.get_fhir_drug_received_code()
        )
        payload.extension.append(extension)
        fhir_payload.append(payload)

        # assesment
        payload = {}
        payload['contentString'] = self._TEST_ASESSMENT
        payload = CommunicationPayload(**payload)
        payload.extension = []

        extension = Extension.construct()
        extension.url = url
        extension.valueCodeableConcept = CommunicationConverter.build_codeable_concept(
            system=system,
            code=Config.get_fhir_asessment_code()
        )
        payload.extension.append(extension)

        fhir_payload.append(payload)

        fhir_communication.payload = fhir_payload

        fhir_communication.about = [CommunicationConverter.build_fhir_resource_reference(
            self._TEST_CLAIM,
            type="Claim",
        )]

        fhir_communication.subject = CommunicationConverter.build_fhir_resource_reference(
            self._TEST_CLAIM.insuree,
            type="Patient",
        )

        return fhir_communication

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual("completed", fhir_obj.status)
        self.assertIn(self._TEST_INSUREE_UUID, fhir_obj.subject.reference)
        self.assertIn(self._TEST_CLAIM_UUID, fhir_obj.about[0].reference)
        for payload in fhir_obj.payload:
            code = payload.extension[0].valueCodeableConcept.coding[0].code
            content_string = payload.contentString
            if code != Config.get_fhir_asessment_code():
                bool_value = self._convert_bool_value(content_string)
            if code == Config.get_fhir_care_rendered_code():
                self.assertEqual(self._TEST_CARE_RENDERED, bool_value)
            elif code == Config.get_fhir_payment_asked_code():
                self.assertEqual(self._TEST_PAYMENT_ASKED, bool_value)
            elif code == Config.get_fhir_drug_prescribed_code():
                self.assertEqual(self._TEST_DRUG_PRESCRIBED, bool_value)
            elif code == Config.get_fhir_drug_received_code():
                self.assertEqual(self._TEST_DRUG_RECEIVED, bool_value)
            elif code == Config.get_fhir_asessment_code():
                self.assertEqual(self._TEST_ASESSMENT, content_string)

    def _convert_bool_value(self, fhir_content_string):
        if fhir_content_string == "yes":
            return True
        if fhir_content_string == "no":
            return False
        return None
