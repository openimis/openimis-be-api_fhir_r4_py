from policy.services import EligibilityResponse, EligibilityRequest
from insuree.test_helpers import create_test_insuree
from medical.test_helpers import create_test_service, create_test_item

from api_fhir_r4.configurations import GeneralConfiguration, R4CoverageEligibilityConfiguration as Config
from api_fhir_r4.converters import PatientConverter
from api_fhir_r4.models import CoverageEligibilityRequestV2 as CoverageEligibilityRequest
from fhir.resources.R4B.coverageeligibilityrequest import CoverageEligibilityRequestItem
from api_fhir_r4.tests import GenericTestMixin
from api_fhir_r4.utils import TimeUtils


class CoverageEligibilityRequestTestMixin(GenericTestMixin):
    _TEST_ADMIN_USER_ID = 1
    _TEST_ADMIN_USER_UUID = "90b0cee2-73ae-4705-af8d-8fe035209ab2"
    _TEST_SERVICE_CODE = 'STEST'
    _TEST_ITEM_CODE = 'ITEST'
    _TEST_CHFID = 'chfid'
    _TEST_TOTAL_ADMISSIONS = 1
    _TEST_TOTAL_VISITS = 3
    _TEST_TOTAL_CONSULTATIONS = 23
    _TEST_TOTAL_SURGERIES = 5
    _TEST_TOTAL_DELIVERIES = 2
    _TEST_TOTAL_ANTENATAL = 11
    _TEST_CONSULTATION_AMOUNT = 123.21
    _TEST_SURGERY_AMOUNT = 12.11
    _TEST_DELIVERY_AMOUNT = 26.00
    _TEST_HOSPITALIZATION_AMOUNT = 42.00
    _TEST_ANTENATAL_AMOUNT = 59.14
    _TEST_SERVICE_LEFT = 12
    _TEST_ITEM_LEFT = 1
    _TEST_IS_SERVICE_OK = True
    _TEST_IS_ITEM_OK = False

    def setUp(self):
        super(CoverageEligibilityRequestTestMixin, self).setUp()
        self._TEST_INSUREE = create_test_insuree()
        self._TEST_INSUREE.chf_id = self._TEST_CHFID
        self._TEST_INSUREE.save()
        self._TEST_SERVICE = create_test_service('D')
        self._TEST_SERVICE.code = self._TEST_SERVICE_CODE
        self._TEST_SERVICE.save()
        self._TEST_ITEM = create_test_item('D')
        self._TEST_ITEM.code = self._TEST_ITEM_CODE
        self._TEST_ITEM.save()
        self._TEST_ELIGIBILITY_REQUEST = EligibilityRequest(
            self._TEST_CHFID,
            self._TEST_SERVICE_CODE,
            self._TEST_ITEM_CODE
        )

    def create_test_imis_instance(self):
        return EligibilityResponse(
            eligibility_request=self._TEST_ELIGIBILITY_REQUEST,
            prod_id=None,
            total_admissions_left=self._TEST_TOTAL_ADMISSIONS,
            total_visits_left=self._TEST_TOTAL_VISITS,
            total_consultations_left=self._TEST_TOTAL_CONSULTATIONS,
            total_surgeries_left=self._TEST_TOTAL_SURGERIES,
            total_deliveries_left=self._TEST_TOTAL_DELIVERIES,
            total_antenatal_left=self._TEST_TOTAL_ANTENATAL,
            consultation_amount_left=self._TEST_CONSULTATION_AMOUNT,
            surgery_amount_left=self._TEST_SURGERY_AMOUNT,
            delivery_amount_left=self._TEST_DELIVERY_AMOUNT,
            hospitalization_amount_left=self._TEST_HOSPITALIZATION_AMOUNT,
            antenatal_amount_left=self._TEST_ANTENATAL_AMOUNT,
            min_date_service=None,
            min_date_item=None,
            service_left=self._TEST_SERVICE_LEFT,
            item_left=self._TEST_ITEM_LEFT,
            is_item_ok=self._TEST_IS_ITEM_OK,
            is_service_ok=self._TEST_IS_SERVICE_OK
        )

    def verify_imis_instance(self, imis_obj):
        # The reference used to be the CHFID but reference are now all on UUID
        # self.assertEqual(self._TEST_CHFID, imis_obj.chf_id)
        self.assertEqual(str(self._TEST_INSUREE.chf_id), imis_obj.chf_id)
        self.assertEqual(self._TEST_ITEM_CODE, imis_obj.item_code)
        self.assertEqual(self._TEST_SERVICE_CODE, imis_obj.service_code)

    def create_test_fhir_instance(self):
        self.setUp()
        fhir_request = {}
        fhir_request["resourceType"] = "CoverageEligibilityRequest"
        fhir_request["status"] = "active"
        fhir_request["purpose"] = ["benefits"]
        fhir_request["created"] = TimeUtils.date().isoformat()

        reference_patient = {}
        reference_patient["reference"] = f'Patient/{self._TEST_CHFID}'
        fhir_request['patient'] = reference_patient

        reference_insurer = {}
        reference_insurer["reference"] = 'openIMIS'
        fhir_request["insurer"] = reference_insurer

        fhir_request = CoverageEligibilityRequest(**fhir_request)

        fhir_request.item = []
        item = CoverageEligibilityRequestItem.construct()
        item.category = PatientConverter.build_codeable_concept(
            system=f'{GeneralConfiguration.get_base_url()}/CodeSystem/claim-item-category',
            code="service",
            display="Service"
        )
        item.productOrService = PatientConverter.build_simple_codeable_concept(
            text=self._TEST_SERVICE_CODE
        )
        fhir_request.item.append(item)

        item = CoverageEligibilityRequestItem.construct()
        item.category = PatientConverter.build_codeable_concept(
            system=f'{GeneralConfiguration.get_base_url()}/CodeSystem/claim-item-category',
            code="item",
            display="Item"
        )
        item.productOrService = PatientConverter.build_simple_codeable_concept(
            text=self._TEST_ITEM_CODE
        )
        fhir_request.item.append(item)
        return fhir_request

    def verify_fhir_instance(self, fhir_obj):
        self.assertIsNotNone(fhir_obj.insurance[0].item)
        for item in fhir_obj.insurance[0].item:
            if item.category.text == Config.get_fhir_total_admissions_code():
                self.assertEqual(self._TEST_TOTAL_ADMISSIONS, item.benefit[0].allowedUnsignedInt)
            elif item.category.text == Config.get_fhir_total_visits_code():
                self.assertEqual(self._TEST_TOTAL_VISITS, item.benefit[0].allowedUnsignedInt)
            elif item.category.text == Config.get_fhir_total_consultations_code():
                self.assertEqual(self._TEST_TOTAL_CONSULTATIONS, item.benefit[0].allowedUnsignedInt)
            elif item.category.text == Config.get_fhir_total_surgeries_code():
                self.assertEqual(self._TEST_TOTAL_SURGERIES, item.benefit[0].allowedUnsignedInt)
            elif item.category.text == Config.get_fhir_total_deliveries_code():
                self.assertEqual(self._TEST_TOTAL_DELIVERIES, item.benefit[0].allowedUnsignedInt)
            elif item.category.text == Config.get_fhir_total_antenatal_code():
                self.assertEqual(self._TEST_TOTAL_ANTENATAL, item.benefit[0].allowedUnsignedInt)
            elif item.category.text == Config.get_fhir_consultation_amount_code():
                self.assertEqual(str(self._TEST_CONSULTATION_AMOUNT), str(item.benefit[0].allowedMoney.value))
            elif item.category.text == Config.get_fhir_surgery_amount_code():
                self.assertEqual(str(self._TEST_SURGERY_AMOUNT), str(item.benefit[0].allowedMoney.value))
            elif item.category.text == Config.get_fhir_delivery_amount_code():
                self.assertEqual(str(self._TEST_DELIVERY_AMOUNT), str(item.benefit[0].allowedMoney.value))
            elif item.category.text == Config.get_fhir_hospitalization_amount_code():
                self.assertEqual(str(self._TEST_HOSPITALIZATION_AMOUNT), str(item.benefit[0].allowedMoney.value))
            elif item.category.text == Config.get_fhir_antenatal_amount_code():
                self.assertEqual(str(self._TEST_ANTENATAL_AMOUNT), str(item.benefit[0].allowedMoney.value))
            elif item.category.text == Config.get_fhir_service_left_code():
                self.assertEqual(self._TEST_SERVICE_LEFT, item.benefit[0].allowedUnsignedInt)
            elif item.category.text == Config.get_fhir_item_left_code():
                self.assertEqual(self._TEST_ITEM_LEFT, item.benefit[0].allowedUnsignedInt)
            elif item.category.text == Config.get_fhir_is_service_ok_code():
                self.assertEqual(self._TEST_IS_SERVICE_OK, not item.excluded)
            elif item.category.text == Config.get_fhir_is_item_ok_code():
                self.assertEqual(self._TEST_IS_ITEM_OK, not item.excluded)
