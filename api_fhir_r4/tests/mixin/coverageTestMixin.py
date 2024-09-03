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

    _TEST_POLICY = None
    _TEST_POLICY_VALUE = 10000.0
    test_insuree = None
    sub_str = {}

    def setUp(self):
        super(GenericTestMixin, self).setUp()
        self.create_dependencies()
        self.sub_str[self._TEST_INSUREE_CHFID] = self.test_insuree.chf_id
        self.sub_str[self._TEST_PRODUCT_UUID] = self._TEST_PRODUCT.uuid

    @classmethod
    def create_dependencies(cls):
                # create mocked insuree
        cls.test_insuree = create_test_insuree(
            with_family=True,
            custom_props={"chf_id": cls._TEST_INSUREE_CHFID}
        )
        imis_officer = create_test_officer()
        cls._TEST_PRODUCT = create_test_product(cls._TEST_PRODUCT_CODE, valid=True, custom_props={})


        cls._TEST_POLICY = create_test_policy(
            product=cls._TEST_PRODUCT,
            insuree=cls.test_insuree,
            custom_props={
                "uuid": cls._TEST_POLICY_UUID,
                "officer_id": imis_officer.id,
                "family": cls.test_insuree.family,
                'enroll_date': TimeUtils.str_to_date(cls._TEST_POLICY_ENROLL_DATE),
                'effective_date': TimeUtils.str_to_date(cls._TEST_POLICY_EFFECTIVE_DATE),
                'expiry_date': TimeUtils.str_to_date(cls._TEST_POLICY_EXPIRED_DATE),
                'stage': cls._TEST_POLICY_STAGE,
                'status': cls._TEST_POLICY_STATUS,
                'value': cls._TEST_POLICY_VALUE,
            }
        )


    
    def create_test_imis_instance(self):
        return self._TEST_POLICY

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
        self.assertIn(fhir_obj.policyHolder.reference, f"Patient/{self.test_insuree.chf_id}")
        self.assertIn(fhir_obj.beneficiary.reference, f"Patient/{self.test_insuree.chf_id}")
        self.assertIn(fhir_obj.payor[0].reference, f"Patient/{self.test_insuree.chf_id}")
        self.assertEqual(1, len(fhir_obj.class_fhir))
        self.assertEqual('plan', fhir_obj.class_fhir[0].type.coding[0].code)
        self.assertEqual(self._TEST_PRODUCT_CODE, fhir_obj.class_fhir[0].value)
        self.assertEqual(f'{self._TEST_PRODUCT_NAME} {self._TEST_PRODUCT_CODE}', fhir_obj.class_fhir[0].name)
        period = fhir_obj.period
        self.assertEqual(self._TEST_POLICY_START_DATE[:10], period.start.isoformat()[:10])
        self.assertEqual(self._TEST_POLICY_EXPIRED_DATE[:10], period.end.isoformat()[:10])
