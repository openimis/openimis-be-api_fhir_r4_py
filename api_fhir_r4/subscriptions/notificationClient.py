import asyncio
import decimal
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

import aiohttp

from typing import Union, Dict, List, Any, TypeVar, Generic, Iterable

import orjson

from api_fhir_r4.models import Subscription

NOTIFICATION_CONTENT_TYPE = TypeVar('NOTIFICATION_CONTENT_TYPE')  # FHIR INPUT
CLIENT_ACCEPTABLE_CONTENT_TYPE = TypeVar('CLIENT_ACCEPTABLE_CONTENT_TYPE')  # CLIENT INPUT
NOTIFICATION_OUTPUT_TYPE = TypeVar('NOTIFICATION_OUTPUT_TYPE')  # CLIENT RESPONSE

logger = logging.getLogger('openIMIS')


class AbstractAsyncSubscriptionNotificationClient(
        Generic[NOTIFICATION_CONTENT_TYPE, CLIENT_ACCEPTABLE_CONTENT_TYPE, NOTIFICATION_OUTPUT_TYPE], ABC):
    def propagate_notifications(self, notification_content: NOTIFICATION_CONTENT_TYPE, subscribers: List[Subscription])\
            -> Iterable[NOTIFICATION_OUTPUT_TYPE]:
        """
        Create new asyncio event loop and call propagate_notifications_async.

        Args:
            notification_content: Message to be sent to all recipients
            subscribers: List of recipients, eligible for receiving given notification.

        Returns:
            List of responses or errors occurred during notifying subscribers
        """
        return asyncio.run(self.propagate_notifications_async(notification_content, subscribers))

    async def propagate_notifications_async(self, content: NOTIFICATION_CONTENT_TYPE, subscribers: List[Subscription])\
            -> Iterable[NOTIFICATION_OUTPUT_TYPE]:
        payload = self._normalize_payload(content)
        async with aiohttp.ClientSession() as session:
            tasks = []
            for sub in subscribers:
                task = asyncio.ensure_future(self._send_notification_async(payload, sub, session))
                tasks.append(task)
            result = await asyncio.gather(*tasks)
            return result

    @abstractmethod
    def _normalize_payload(self, payload: NOTIFICATION_CONTENT_TYPE) -> CLIENT_ACCEPTABLE_CONTENT_TYPE:
        """
        Transforms payload to format accepted by _send_notification_async

        Args:
            payload: Content of notification being sent to subscribers

        Returns:
            Payload transformed to type acceptable by client.
        """
        pass

    @abstractmethod
    async def _send_notification_async(
            self, content: CLIENT_ACCEPTABLE_CONTENT_TYPE, subscriber: Subscription,
            client_session: aiohttp.ClientSession) -> NOTIFICATION_OUTPUT_TYPE:
        """
        Uses client_session for sending content to designated subscriber.

        @param content: Content of notification
        @param subscriber: Recipient of the notification
        @param client_session: Open client session responsible for sending content.
        @return:
        """
        pass


RestNotificationContentType = Union[Dict, str]


@dataclass
class SubscriberNotificationOutput:
    subscription: Subscription
    notification_success: bool
    reason_of_failure: Any = None


class RestSubscriptionNotificationClient(AbstractAsyncSubscriptionNotificationClient[
                                RestNotificationContentType, Union[str, bytes], SubscriberNotificationOutput]):
    async def _send_notification_async(self, content: CLIENT_ACCEPTABLE_CONTENT_TYPE, subscriber: Subscription,
                                       client_session: aiohttp.ClientSession) -> NOTIFICATION_OUTPUT_TYPE:
        try:
            post_args = self._post_args(content, subscriber)
            async with client_session.post(**post_args) as post:
                response = await post.json()
                status = post.status
                if status >= 400:
                    return SubscriberNotificationOutput(subscriber, False, response)
                else:
                    return SubscriberNotificationOutput(subscriber, True, None)
        except Exception as e:
            logger.error(F"Sending subscription notification has failed due to {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return SubscriberNotificationOutput(subscriber, False, e)

    def _normalize_payload(self, payload: NOTIFICATION_CONTENT_TYPE) -> CLIENT_ACCEPTABLE_CONTENT_TYPE:
        return payload if isinstance(payload, str) else self.__transform_payload(payload)

    @property
    def _base_headers(self):
        return {
            'content-type': 'application/json',
            'accept': 'application/json'
        }

    @staticmethod
    def __transform_payload(payload):
        def uuid_convert(o):
            if isinstance(o, uuid.UUID):
                return o.hex
            if isinstance(o, decimal.Decimal):
                return float(o)
        return orjson.dumps(payload, default=uuid_convert)

    def _post_args(self, content, subscriber: Subscription):
        try:
            subscriber_headers = json.loads(subscriber.headers)
        except TypeError as e:
            logger.debug(f"Notification failed due to invalid headers format: {subscriber.headers}.")
            raise TypeError(f"Invalid format of headers for '{subscriber}'."
                            f" Headers should be provided as JSON string.") \
                from e
        return {
            'headers': {**self._base_headers, **subscriber_headers},
            'url': subscriber.endpoint,
            'data': content
        }
