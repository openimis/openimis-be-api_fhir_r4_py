import datetime
import os
from functools import lru_cache
from unittest import mock, TestCase

from claim.models import ClaimItem, ClaimService
from location.models import HealthFacility
from medical.models import Diagnosis, Item, Service
from prompt_toolkit.cache import memoized

from api_fhir_r4.converters import ClaimResponseConverter, ConditionConverter, HealthcareServiceConverter
from api_fhir_r4.models import FHIRBaseObject, ClaimResponseError, CodeableConcept, Coding, Extension, Period, \
    ClaimResponsePayment
from api_fhir_r4.tests import ClaimResponseTestMixin


class ClaimResponseConverterTestCase(ClaimResponseTestMixin):

    __TEST_CLAIM_RESPONSE_JSON_PATH = "/test/test_claimResponse.json"

    def setUp(self):
        super(ClaimResponseConverterTestCase, self).setUp()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self._test_claim_response_json_representation = open(dir_path + self.__TEST_CLAIM_RESPONSE_JSON_PATH).read()
        if self._test_claim_response_json_representation[-1:] == "\n":
            self._test_claim_response_json_representation = self._test_claim_response_json_representation[:-1]

    @mock.patch('claim.models.ClaimItem.objects')
    @mock.patch('claim.models.ClaimService.objects')
    def test_to_fhir_obj(self, cs_mock, ci_mock):
        cs_mock.filter.return_value = [self._TEST_SERVICE]
        ci_mock.filter.return_value = [self._TEST_ITEM]

        imis_claim_response = self.create_test_imis_instance()
        item = self.create_test_claim_item()
        item.claim = imis_claim_response
        item.item.save()
        item.save()
        service = self.create_test_claim_service()
        service.claim = imis_claim_response
        service.service.save()
        service.save()
        fhir_claim_response = ClaimResponseConverter.to_fhir_obj(imis_claim_response)
        self.verify_fhir_instance(fhir_claim_response)

    # def test_fhir_object_to_json_request(self):
    #     fhir_obj = self.create_test_fhir_instance()
    #     actual_representation = fhir_obj.dumps(format_='json')
    #     self.assertEqual(self._test_claim_response_json_representation, actual_representation)

    # def test_create_object_from_json(self):
    #     fhir_claim = FHIRBaseObject.loads(self._test_claim_response_json_representation, 'json')
    #     self.verify_fhir_instance(fhir_claim)

    def test_fhir_object_to_imis_object(self):
        expected_claim, fhir_obj = self.get_or_create_test_data()
        actual_claim = ClaimResponseConverter.to_imis_obj(fhir_obj, 1)
        self.assertEqual(expected_claim, actual_claim)

    def test_build_imis_outcome(self):
        claim, fhir_obj = self.get_or_create_test_data()
        fhir_obj.outcome = 'checked'
        ClaimResponseConverter.build_imis_outcome(claim, fhir_obj)
        self.assertEqual(claim.status, 4)

    def test_build_imis_errors(self):
        claim, fhir_obj = self.get_or_create_test_data()
        test_error = ClaimResponseError()
        test_error.code = self.build_test_codeable_concept(str(10))
        fhir_obj.error = [test_error]
        ClaimResponseConverter.build_imis_errors(claim, fhir_obj)
        self.assertEqual(claim.rejection_reason, 10)

    def test_build_imis_type(self):
        claim, fhir_obj = self.get_or_create_test_data()
        fhir_obj.type = self.build_test_codeable_concept(None, 'E')
        ClaimResponseConverter.build_imis_type(claim, fhir_obj)
        self.assertEqual(claim.visit_type, 'E')

    def test_build_imis_status(self):
        claim, fhir_obj = self.get_or_create_test_data()
        fhir_obj.status = "Not Selected"
        ClaimResponseConverter.build_imis_status(claim, fhir_obj)
        self.assertEqual(claim.review_status, 2)

    def test_build_imis_requestor(self):
        claim, fhir_obj = self.get_or_create_test_data()
        hf = HealthFacility.objects.get(id=2)
        fhir_obj.requestor = HealthcareServiceConverter.build_fhir_resource_reference(hf)
        ClaimResponseConverter.build_imis_requestor(claim, fhir_obj)
        self.assertEqual(claim.health_facility, hf)

    def test_build_imis_billable_period(self):
        claim, fhir_obj = self.get_or_create_test_data()
        date_from = datetime.date(2020, 10, 5)
        date_to = datetime.date(2020, 11, 5)
        fhir_obj.extension = [self.build_test_billable_period_extension_concept(date_from, date_to)]
        ClaimResponseConverter.build_imis_billable_period(claim, fhir_obj)
        self.assertEqual(claim.date_from, date_from)
        self.assertEqual(claim.date_to, date_to)

    def test_build_imis_diagnoses(self):
        claim, fhir_obj = self.get_or_create_test_data()
        d1 = self.build_test_diagonosis('D1')
        d1.save()
        d2 = self.build_test_diagonosis('D2')
        d2.save()
        fhir_obj.extension = [
            self.build_diagnosis_extensions('icd_0', d1),
            self.build_diagnosis_extensions('icd_1', d2),
        ]
        ClaimResponseConverter.build_imis_diagnoses(claim, fhir_obj)
        self.assertEqual(claim.icd, d1)
        self.assertEqual(claim.icd_1, d2)

    def test_build_imis_adjustment(self):
        claim, fhir_obj = self.get_or_create_test_data()
        adjustment = 'TestAdjustment1'
        fhir_obj.payment = self.build_test_adjustment(adjustment)
        ClaimResponseConverter.build_imis_adjustment(claim, fhir_obj)
        self.assertEqual(claim.adjustment, adjustment)

    def test_build_imis_items(self):
        claim, fhir_obj = self.get_or_create_test_data()

        claim_items = list(ClaimItem.objects.filter(claim=claim))
        claim_services = list(ClaimService.objects.filter(claim=claim))

        ClaimResponseConverter.build_imis_items(claim, fhir_obj)

        self.assertListEqual(claim.claim_items, claim_items)
        self.assertListEqual(claim.claim_services, claim_services)

    @lru_cache(maxsize=None)
    def get_or_create_test_data(self):
        imis_instance = self.create_test_imis_instance()
        imis_instance.health_facility = HealthFacility.objects.get(id=1)
        imis_instance.icd.save()
        imis_instance.save()

        item = self.build_claim_item(imis_instance)
        item.save()

        service = self.build_claim_service(imis_instance)
        service.save()

        fhir_instance = ClaimResponseConverter.to_fhir_obj(imis_instance)
        return imis_instance, fhir_instance

    def build_test_codeable_concept(self, code=None, text=None):
        codeable_concept = CodeableConcept()
        if code:
            coding = Coding()
            if not isinstance(code, str):
                code = str(code)
            coding.code = code
            codeable_concept.coding = [coding]
        if text:
            codeable_concept.text = text
        return codeable_concept

    def build_test_billable_period_extension_concept(self, date_from=None, date_to=None):
        extension = Extension()
        extension.url = "billablePeriod"
        extension.valuePeriod = Period()
        if date_from:
            extension.valuePeriod.start = date_from.isoformat()
        if date_to:
            extension.valuePeriod.end = date_to.isoformat()
        return extension

    def build_diagnosis_extensions(self, icd_order, diagnosis):
        extension = Extension()
        extension.url = icd_order
        extension.valueReference = ConditionConverter.build_fhir_resource_reference(diagnosis)
        return extension

    def build_test_adjustment(self, adjustment):
        fhir_payment = ClaimResponsePayment()
        fhir_payment.adjustmentReason = self.build_test_codeable_concept(None, adjustment)
        return fhir_payment

    def build_test_diagonosis(self, code):
        d = Diagnosis(code=code)
        d.audit_user_id = self._ADMIN_AUDIT_USER_ID
        return d

    def build_claim_item(self, claim):
        item = Item.objects.get(id=1)
        claim_item = ClaimItem()
        claim_item.claim = claim
        claim_item.item = item
        claim_item.status = 4
        claim_item.availability = True
        claim_item.audit_user_id = 1
        self.assign_default_qty(claim_item)
        self.assign_default_prices(claim_item)
        return claim_item

    def build_claim_service(self, claim):
        service = Service.objects.get(id=1)
        claim_service = ClaimService()
        claim_service.claim = claim
        claim_service.service = service
        claim_service.status = 2
        claim_service.audit_user_id = 1
        self.assign_default_qty(claim_service)
        self.assign_default_prices(claim_service)
        return claim_service

    def assign_default_qty(self, claim_item):
        claim_item.qty_provided = 10
        claim_item.qty_approved = 9

    def assign_default_prices(self, claim_item):
        claim_item.price_asked = 100
        claim_item.price_approved = 90
        claim_item.price_adjusted = 90
        claim_item.price_valuated = 90
