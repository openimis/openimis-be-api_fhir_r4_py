import core
import uuid

from policy.test_helpers import create_test_policy
from insuree.models import InsureePolicy

from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.converters.coverageConverter import CoverageConverter
from api_fhir_r4.tests import GenericTestMixin

from api_fhir_r4.utils import TimeUtils

from core.test_helpers import create_test_officer
from insuree.test_helpers import create_test_insuree
from product.test_helpers import create_test_product


class CoverageTestMixin(GenericTestMixin):

    _TEST_POLICY_UUID = "f88687a7-1f33-466b-8c74-8b7173dc5583"
    _TEST_POLICY_ENROLL_DATE = "2021-08-20"
    _TEST_POLICY_START_DATE = "2021-08-20T00:00:00"
    _TEST_POLICY_EFFECTIVE_DATE = "2021-08-20"
    _TEST_POLICY_EXPIRED_DATE = "2022-08-19T00:00:00"
    _TEST_POLICY_STATUS = 1
    _TEST_POLICY_STAGE = 'N'
    _TEST_PRODUCT_CODE = "T0001"
    _TEST_PRODUCT_NAME = "Test product"
    _TEST_INSUREE_CHFID = 'chfid1'
    _TEST_PRODUCT_UUID = "8ed8d2d9-2644-4d29-ba37-ab772386cfca"

    _TEST_POLICY_VALUE = 10000.0

    def create_test_imis_instance(self):
        # create mocked insuree
        imis_insuree = create_test_insuree(
            with_family=True,
            custom_props={"chf_id": self._TEST_INSUREE_CHFID}
        )

        # update family uuid
        imis_family = imis_insuree.family
        # create mocked product

        imis_officer = create_test_officer()
        imis_product = create_test_product(self._TEST_PRODUCT_CODE, valid=True, custom_props=None)
        imis_product.uuid = self._TEST_PRODUCT_UUID
        imis_product.save()

        imis_policy = create_test_policy(
            product=imis_product,
            insuree=imis_insuree,
            custom_props={
                "uuid": self._TEST_POLICY_UUID,
                "officer_id": imis_officer.id,
                "family":imis_insuree.family
            }
        )

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
        self.assertEqual(self._TEST_PRODUCT_CODE, imis_obj.product.code)
        self.assertEqual(self._TEST_PRODUCT_UUID, str(uuid.UUID(imis_obj.product.uuid)))

    def verify_fhir_instance(self, fhir_obj):
        for identifier in fhir_obj.identifier:
            code = CoverageConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_uuid_type_code():
                self.assertEqual(self._TEST_POLICY_UUID, identifier.value)
        self.assertIn(f"Patient/{self._TEST_INSUREE_CHFID}", fhir_obj.policyHolder.reference)
        self.assertIn(f"Patient/{self._TEST_INSUREE_CHFID}", fhir_obj.beneficiary.reference)
        self.assertIn(f"Patient/{self._TEST_INSUREE_CHFID}", fhir_obj.payor[0].reference)
        self.assertEqual(1, len(fhir_obj.class_fhir))
        self.assertEqual('plan', fhir_obj.class_fhir[0].type.coding[0].code)
        self.assertEqual(self._TEST_PRODUCT_CODE, fhir_obj.class_fhir[0].value)
        self.assertEqual(f'{self._TEST_PRODUCT_NAME} {self._TEST_PRODUCT_CODE}', fhir_obj.class_fhir[0].name)
        period = fhir_obj.period
        self.assertEqual(self._TEST_POLICY_START_DATE[:10], period.start.isoformat()[:10])
        self.assertEqual(self._TEST_POLICY_EXPIRED_DATE[:10], period.end.isoformat()[:10])
