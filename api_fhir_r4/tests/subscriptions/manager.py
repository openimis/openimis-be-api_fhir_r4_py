import datetime

from asynctest import MagicMock
from django.test import TestCase

from api_fhir_r4.converters import ClaimConverter, ReferenceConverterMixin
from api_fhir_r4.models import Subscription, SubscriptionNotificationResult
from api_fhir_r4.subscriptions.notificationClient import RestSubscriptionNotificationClient, \
    SubscriberNotificationOutput
from api_fhir_r4.subscriptions.notificationManager import RestSubscriptionNotificationManager
from api_fhir_r4.tests import CommunicationTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin


class AsyncContextManagerMock(MagicMock):

    async def __aenter__(self):
        return self.aenter

    async def __aexit__(self, *args):
        pass


class TestSubscriptionNotificationManager(CommunicationTestMixin, LogInMixin, TestCase):
    TEST_HEADERS_1 = """{"test-header": "123", "Authentication": "Bearer ABF13816"}"""
    EXPECTED_HEADER_1 = {'content-type': 'application/json', 'accept': 'application/json', 'test-header': '123', 'Authentication': 'Bearer ABF13816'}
    TEST_HEADERS_2 = """{"test-header": "123", "Authentication": "Bearer 61831FAB"}"""
    EXPECTED_HEADER_2 = {'content-type': 'application/json', 'accept': 'application/json', 'test-header': '123', 'Authentication': 'Bearer 61831FAB'}
    NOTIFICATION_CONTENT = {'notification_content': 'content'}

    def setUp(self) -> None:
        super().setUp()
        self._test_user = self.get_or_create_user_api()
        self._test_subscriptions = self._create_test_subscriptions()
        self._test_resource = self.create_test_claim()
        self._test_converter = ClaimConverter()

    def test_sending_claim_notification(self):
        mocked_client = MagicMock()
        mocked_client.propagate_notifications = MagicMock()
        mocked_client.propagate_notifications.return_value = [
            SubscriberNotificationOutput(self._test_subscriptions[0], True),
            SubscriberNotificationOutput(self._test_subscriptions[1], False, {"ServerError": "Endpoint Unavailable"})
        ]
        test_manger = RestSubscriptionNotificationManager(fhir_converter=self._test_converter, client=mocked_client)
        test_manger.notify_subscribers_with_resource(self._test_resource, self._test_subscriptions)

        self._assert_mock_call(mocked_client)
        self._assert_saved_result()

    def _create_test_subscriptions(self):
        _valid_subscription = [self._create_valid(self.TEST_HEADERS_1), self._create_valid(self.TEST_HEADERS_2)]
        return _valid_subscription

    def _create_valid(self, headers):
        sub = Subscription(
            status=1, channel=0, endpoint='http://test-subscription-endpoint.io/post_uri/',
            headers=headers, expiring=datetime.datetime.now() + datetime.timedelta(days=10)
        )
        sub.save(username=self._test_user.username)
        return sub

    def _assert_mock_call(self, mocked_client):
        mocked_client.propagate_notifications.assert_called_with(
            self._test_converter.to_fhir_obj(self._test_resource, ReferenceConverterMixin.UUID_REFERENCE_TYPE),
            self._test_subscriptions
        )

    def _assert_saved_result(self):
        success = SubscriptionNotificationResult.objects.subscriber_notifications(self._test_subscriptions[0])
        failure = SubscriptionNotificationResult.objects.subscriber_notifications(self._test_subscriptions[1])
        self.assertEqual(len(success), 1)
        self.assertEqual(len(failure), 1)
        success, failure = success.first(), failure.first()
        self.assertTrue(success.notified_successfully)
        self.assertFalse(failure.notified_successfully)
        self.assertEqual(failure.error, """{'ServerError': 'Endpoint Unavailable'}""")
