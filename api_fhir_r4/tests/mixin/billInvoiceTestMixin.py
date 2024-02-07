from unittest import mock

from django.contrib.contenttypes.models import ContentType

from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.tests import GenericTestMixin
from api_fhir_r4.tests.mixin import FhirConverterTestMixin
from insuree.models import Family
from insuree.test_helpers import create_test_insuree
from invoice.models import Bill, BillItem
from fhir.resources.R4B.invoice import Invoice as FHIRInvoice
from api_fhir_r4.utils.timeUtils import TimeUtils
from api_fhir_r4.tests.utils import get_connection_payload,get_or_create_user_api

class BillInvoiceTestMixin(GenericTestMixin, FhirConverterTestMixin):
    _TEST_BILL_STATUS = 'active'
    _TEST_BILL_UUID = '12345678-1234-1234-1234-123456789012'
    _TEST_BILL_CODE = 'TEST-CODE'
    _TEST_BILL_SUBJECT_TYPE = None
    _TEST_BILL_SUBJECT_TYPE_CODING = 'claim-batch'
    _TEST_BILL_THIRD_PARTY = None
    _TEST_BILL_THIRD_PARTY_UUID = '98765432-1234-1234-1234-123456789012'
    _TEST_BILL_DATE = TimeUtils.str_iso_to_date('2021-01-01')
    _TEST_BILL_TOTAL_NET = 10000.0
    _TEST_BILL_TOTAL_GROSS = 10000.0
    _TEST_BILL_CURRENCY = 'USD'
    _TEST_LINE_ITEM_CHARGE_ITEM = None
    _TEST_LINE_ITEM_CHARGE_ITEM_CODING = 'claim'
    _TEST_LiNE_ITEM_QUANTITY = 2
    _TEST_LINE_ITEM_UNIT_PRICE = 5000.0
    _TEST_LINE_ITEM_BASE_PRICE_COMPONENT_TYPE = 'base'
    _TEST_LINE_ITEM_DISCOUNT_COMPONENT_TYPE = 'discount'
    _TEST_LINE_ITEM_DISCOUNT = 0.1
    _TEST_LINE_ITEM_DEDUCTION_PRICE_COMPONENT_TYPE = 'deduction'
    _TEST_LINE_ITEM_DEDUCTION = 100
    _TEST_LINE_ITEM_DEDUCTION_FACTOR = 1
    _TEST_LINE_ITEM_TAX_PRICE_COMPONENT_TYPE = 'tax'
    _TEST_LINE_ITEM_TAX_RATE = 0.02
    user = None
    @classmethod
    def setUpTestData(cls):
        cls.user = get_or_create_user_api()
        cls._TEST_BILL_SUBJECT_TYPE = ContentType.objects.get(model__iexact='BatchRun')
        cls._TEST_LINE_ITEM_CHARGE_ITEM = ContentType.objects.get(model__iexact='Claim')

    def create_test_imis_instance(self):
        self._TEST_BILL_INSUREE = create_test_insuree()
        imis_bill = Bill()
        imis_bill.code = self._TEST_BILL_CODE
        
        imis_bill.subject_type = self._TEST_BILL_SUBJECT_TYPE
        imis_bill.thirdparty = self._TEST_BILL_INSUREE.family
        imis_bill.thirdparty.uuid = self._TEST_BILL_THIRD_PARTY_UUID
        imis_bill.date_bill = self._TEST_BILL_DATE
        imis_bill.amount_net = self._TEST_BILL_TOTAL_NET
        imis_bill.amount_total = self._TEST_BILL_TOTAL_GROSS
        imis_bill.currency_code = self._TEST_BILL_CURRENCY
        imis_bill.save(user=self.user)
        self._TEST_BILL_UUID  =imis_bill.id
        imis_bill_line_item = BillItem()
        imis_bill_line_item.bill = imis_bill
        imis_bill_line_item.line_type = self._TEST_LINE_ITEM_CHARGE_ITEM
        imis_bill_line_item.quantity = self._TEST_LiNE_ITEM_QUANTITY
        imis_bill_line_item.unit_price = self._TEST_LINE_ITEM_UNIT_PRICE
        imis_bill_line_item.discount = self._TEST_LINE_ITEM_DISCOUNT
        imis_bill_line_item.deduction = self._TEST_LINE_ITEM_DEDUCTION
        imis_bill_line_item.tax_rate = None
        imis_bill_line_item.code = "1"
        imis_bill_line_item.save(user=self.user)

        with mock.patch('django.db.models.fields.related_descriptors.create_reverse_many_to_one_manager') as mock_patch:
            class MockedManager(mock.MagicMock):
                def all(self):
                    return [imis_bill_line_item]

            mock_patch.return_value = MockedManager()
            # noinspection PyStatementEffect,PyUnresolvedReferences
            imis_bill.line_items_bill  # This call assigns mocked related manager to the model

        return imis_bill

    def verify_imis_instance(self, imis_obj):
        raise NotImplementedError('verify_imis_instance() not implemented')

    def create_test_fhir_instance(self):
        raise NotImplementedError('create_test_fhir_instance() not implemented')

    def verify_fhir_instance(self, fhir_obj):
        self.assertIs(type(fhir_obj), FHIRInvoice)
        self.assertEqual(fhir_obj.status, self._TEST_BILL_STATUS)
        self.verify_fhir_identifier(fhir_obj, R4IdentifierConfig.get_fhir_uuid_type_code(), self._TEST_BILL_UUID)
        self.verify_fhir_identifier(fhir_obj, R4IdentifierConfig.get_fhir_generic_type_code(), self._TEST_BILL_CODE)
        self.verify_fhir_coding_exists(fhir_obj.type.coding, self._TEST_BILL_SUBJECT_TYPE_CODING)
        self.assertTrue(self._TEST_BILL_THIRD_PARTY_UUID in fhir_obj.recipient.reference)
        self.assertEqual(fhir_obj.date, self._TEST_BILL_DATE)
        self.assertEqual(fhir_obj.totalNet.value, self._TEST_BILL_TOTAL_NET, 1e-10)
        self.assertEqual(fhir_obj.totalNet.currency, self._TEST_BILL_CURRENCY)
        self.assertEqual(fhir_obj.totalGross.value, self._TEST_BILL_TOTAL_GROSS, 1e-10)
        self.assertEqual(fhir_obj.totalGross.currency, self._TEST_BILL_CURRENCY)

        self.assertGreater(len(fhir_obj.lineItem), 0)
        self.verify_fhir_coding_exists(fhir_obj.lineItem[0].chargeItemCodeableConcept.coding,
                                       self._TEST_LINE_ITEM_CHARGE_ITEM_CODING)
        self.assertGreater(len(fhir_obj.lineItem[0].priceComponent), 0)
        for price_component in fhir_obj.lineItem[0].priceComponent:
            if price_component.type == self._TEST_LINE_ITEM_BASE_PRICE_COMPONENT_TYPE:
                self.verify_price_component(price_component, self._TEST_LiNE_ITEM_QUANTITY,
                                            self._TEST_LINE_ITEM_UNIT_PRICE * self._TEST_LiNE_ITEM_QUANTITY,
                                            self._TEST_LINE_ITEM_BASE_PRICE_COMPONENT_TYPE)
            elif price_component.type == self._TEST_LINE_ITEM_DISCOUNT_COMPONENT_TYPE:
                self.verify_price_component(price_component, self._TEST_LINE_ITEM_DISCOUNT,
                                            -self._TEST_LINE_ITEM_UNIT_PRICE * self._TEST_LiNE_ITEM_QUANTITY * (
                                                self._TEST_LINE_ITEM_DISCOUNT),
                                            self._TEST_LINE_ITEM_DISCOUNT_COMPONENT_TYPE)
            elif price_component.type == self._TEST_LINE_ITEM_DEDUCTION_PRICE_COMPONENT_TYPE:
                self.verify_price_component(price_component, self._TEST_LINE_ITEM_DEDUCTION_FACTOR,
                                            -self._TEST_LINE_ITEM_DEDUCTION,
                                            self._TEST_LINE_ITEM_DEDUCTION_PRICE_COMPONENT_TYPE)
            # FIXME tax rate is more complex, requires an object
            # elif price_component.type == self._TEST_LINE_ITEM_TAX_PRICE_COMPONENT_TYPE:
            #     self.verify_price_component(price_component, self._TEST_LINE_ITEM_TAX_RATE,
            #                                 ((self._TEST_LINE_ITEM_UNIT_PRICE * self._TEST_LiNE_ITEM_QUANTITY * (
            #                                         1 - self._TEST_LINE_ITEM_DISCOUNT))
            #                                  - self._TEST_LINE_ITEM_DEDUCTION) * self._TEST_LINE_ITEM_TAX_RATE,
            #                                 self._TEST_LINE_ITEM_TAX_PRICE_COMPONENT_TYPE)

    def verify_price_component(self, price_component, expected_factor, expected_amount, expected_type):
        self.assertGreater(len(price_component.extension), 0)
        self.assertEqual(price_component.extension[0].valueMoney.currency, self._TEST_BILL_CURRENCY)
        self.assertEqual(price_component.extension[0].valueMoney.value, self._TEST_LINE_ITEM_UNIT_PRICE)
        if expected_type:
            self.assertEqual(price_component.type, expected_type)
        self.assertEqual(float(price_component.factor), expected_factor, 1e-10)
        self.assertEqual(float(price_component.amount.value), expected_amount, 1e-10)
