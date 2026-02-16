from api_fhir_r4.models import Subscription
from api_fhir_r4.tests import GenericTestMixin
from api_fhir_r4.utils import TimeUtils

from fhir.resources.R4B.subscription import Subscription as FHIRSubscription


class SubscriptionTestMixin(GenericTestMixin):
    _TEST_SUB_ENDPOINT = "https://test.com/test"
    _TEST_SUB_HEADERS = "TestKey1=TestValue1&TestKey2=TestValue2"
    _TEST_SUB_IMIS_EXPIRING = "2020-01-01T00:00:00+00:00"

    _TEST_SUB_IMIS_CRITERIA = {"resource": "Patient", "chfid__startswith": "0"}
    _TEST_SUB_IMIS_STATUS = 1
    _TEST_SUB_IMIS_CHANNEL = 1

    _TEST_SUB_FHIR_STATUS = "active"
    _TEST_SUB_FHIR_REASON = "Patient"
    _TEST_SUB_FHIR_CRITERIA = "Patient?chfid__startswith=0"
    _TEST_SUB_FHIR_CHANNEL_TYPE = "rest-hook"

    def create_test_imis_instance(self):
        return Subscription(
            **{
                "status": self._TEST_SUB_IMIS_STATUS,
                "channel": self._TEST_SUB_IMIS_CHANNEL,
                "endpoint": self._TEST_SUB_ENDPOINT,
                "headers": self._TEST_SUB_HEADERS,
                "criteria": self._TEST_SUB_IMIS_CRITERIA,
                "expiring": TimeUtils.str_iso_to_date(self._TEST_SUB_IMIS_EXPIRING),
            }
        )

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(imis_obj.status, self._TEST_SUB_IMIS_STATUS)
        self.assertEqual(imis_obj.channel, self._TEST_SUB_IMIS_CHANNEL)
        self.assertEqual(imis_obj.endpoint, self._TEST_SUB_ENDPOINT)
        self.assertEqual(imis_obj.headers, self._TEST_SUB_HEADERS)
        self.assertEqual(imis_obj.criteria, self._TEST_SUB_IMIS_CRITERIA)
        self.assertEqual(
            imis_obj.expiring, TimeUtils.str_iso_to_date(self._TEST_SUB_IMIS_EXPIRING)
        )

    def create_test_fhir_instance(self):
        return FHIRSubscription.parse_obj(
            {
                "status": self._TEST_SUB_FHIR_STATUS,
                "criteria": self._TEST_SUB_FHIR_CRITERIA,
                "end": self._TEST_SUB_IMIS_EXPIRING,
                "reason": self._TEST_SUB_FHIR_REASON,
                "channel": {
                    "type": self._TEST_SUB_FHIR_CHANNEL_TYPE,
                    "endpoint": self._TEST_SUB_ENDPOINT,
                    "header": [self._TEST_SUB_HEADERS],
                },
            }
        )

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual(fhir_obj.status, self._TEST_SUB_FHIR_STATUS)
        self.assertEqual(fhir_obj.criteria, self._TEST_SUB_FHIR_CRITERIA)
        self.assertEqual(
            fhir_obj.end, TimeUtils.str_iso_to_date(self._TEST_SUB_IMIS_EXPIRING)
        )
        self.assertEqual(fhir_obj.channel.type, self._TEST_SUB_FHIR_CHANNEL_TYPE)
        self.assertEqual(fhir_obj.channel.endpoint, self._TEST_SUB_ENDPOINT)
        self.assertEqual(fhir_obj.channel.header, [self._TEST_SUB_HEADERS])
