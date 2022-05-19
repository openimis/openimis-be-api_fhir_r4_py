import asyncio
import datetime

from asynctest import CoroutineMock, MagicMock, patch, call
from asgiref.sync import async_to_sync
from django.test import TestCase

from api_fhir_r4.models import Subscription
from api_fhir_r4.subscriptions.notificationClient import RestSubscriptionNotificationClient, \
    SubscriberNotificationOutput
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from aiohttp import web


class AsyncContextManagerMock(MagicMock):

    async def __aenter__(self):
        return self.aenter

    async def __aexit__(self, *args):
        pass


class TestSubscriptionNotificationClient(LogInMixin, TestCase):
    TEST_HEADERS_1 = """{"test-header": "123", "Authentication": "Bearer ABF13816"}"""
    EXPECTED_HEADER_1 = {'content-type': 'application/json', 'accept': 'application/json', 'test-header': '123', 'Authentication': 'Bearer ABF13816'}
    TEST_HEADERS_2 = """{"test-header": "123", "Authentication": "Bearer 61831FAB"}"""
    EXPECTED_HEADER_2 = {'content-type': 'application/json', 'accept': 'application/json', 'test-header': '123', 'Authentication': 'Bearer 61831FAB'}
    NOTIFICATION_CONTENT = {'notification_content': 'content'}

    def setUp(self) -> None:
        super().setUp()
        self._test_user = self.get_or_create_user_api()
        self._test_subscriptions = self._create_test_subscriptions()

    @async_to_sync
    @patch("api_fhir_r4.subscriptions.notificationClient.aiohttp.ClientSession.post")
    async def test_post_should_propagate_correctly(self, session):
        session.return_value.__aenter__.return_value.json = CoroutineMock(side_effect=
            [{'Notification': 'Thanks for notification'}, {'Notification': 'Thanks for notification'}])
        session.return_value.__aenter__.return_value.status = 200
        sub_client = RestSubscriptionNotificationClient()
        response = await sub_client.propagate_notifications_async(self.NOTIFICATION_CONTENT, self._test_subscriptions)

        expected = [SubscriberNotificationOutput(self._test_subscriptions[0], True, None),
                    SubscriberNotificationOutput(self._test_subscriptions[1], True, None)]
        self.assertListEqual(expected, list(response))

        session.assert_any_call(
            url='http://test-subscription-endpoint.io/post_uri/',
            headers=self.EXPECTED_HEADER_1, data=b'{"notification_content":"content"}')
        session.assert_any_call(
            url='http://test-subscription-endpoint.io/post_uri/',
            headers=self.EXPECTED_HEADER_2, data=b'{"notification_content":"content"}')

    @async_to_sync
    @patch("api_fhir_r4.subscriptions.notificationClient.aiohttp.ClientSession.post")
    async def test_post_server_unavailable(self, session):
        server_response = {'Notification': 'Server offline'}
        session.return_value.__aenter__.return_value.json = \
            CoroutineMock(side_effect=[server_response, server_response])
        session.return_value.__aenter__.return_value.status = 503

        sub_client = RestSubscriptionNotificationClient()
        response = await sub_client.propagate_notifications_async(self.NOTIFICATION_CONTENT, self._test_subscriptions)
        expected = [SubscriberNotificationOutput(self._test_subscriptions[0], False, server_response),
                    SubscriberNotificationOutput(self._test_subscriptions[1], False, server_response)]

        self.assertListEqual(expected, list(response))

        session.assert_any_call(
            url='http://test-subscription-endpoint.io/post_uri/',
            headers=self.EXPECTED_HEADER_1, data=b'{"notification_content":"content"}')
        session.assert_any_call(
            url='http://test-subscription-endpoint.io/post_uri/',
            headers=self.EXPECTED_HEADER_2, data=b'{"notification_content":"content"}')

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

    def _mock_coro(self):
        f = asyncio.Future()
        f.set_result(web.Response(text='Thanks for notification.'))
        return f
