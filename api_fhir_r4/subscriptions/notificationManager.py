import logging
from typing import Union, List, Tuple, Iterable

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

import core.datetimes.ad_datetime
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.models import Subscription, SubscriptionNotificationResult
from api_fhir_r4.subscriptions.notificationClient import (
    RestSubscriptionNotificationClient,
    SubscriberNotificationOutput,
)
from api_fhir_r4.subscriptions.resourceRights import notification_refusal
from core.models import HistoryModel, VersionedModel
from core.utils import clear_current_user, get_current_user, set_current_user

logger = logging.getLogger(__name__)


class RestSubscriptionNotificationManager:

    def __init__(
        self,
        fhir_converter: BaseFHIRConverter,
        client: RestSubscriptionNotificationClient = None,
    ):
        if client is None:
            client = RestSubscriptionNotificationClient()
        self.client = client
        # A converter class, or an instance whose class is used: the resource is
        # converted once per subscription owner, as that owner (OP-3351).
        self.converter_class = (
            fhir_converter if isinstance(fhir_converter, type) else type(fhir_converter)
        )

    def notify_subscribers_with_resource(
        self,
        imis_resource: Union[HistoryModel, VersionedModel],
        subscribers: List[Subscription],
    ) -> Iterable[SubscriptionNotificationResult]:
        valid, rejected = self._validate_subscribers(subscribers)
        authorized, refused = self._authorize_subscribers(imis_resource, valid)
        results = [*rejected, *refused]
        for owner, owner_subscribers in self._group_by_owner(authorized):
            try:
                fhir_content = self._resource_to_fhir(imis_resource, owner)
            except Exception as e:
                logger.error(
                    "Converting %s for subscription owner %s failed",
                    imis_resource, owner.id, exc_info=e,
                )
                results.extend(
                    SubscriberNotificationOutput(subscriber, False, "conversion failed")
                    for subscriber in owner_subscribers
                )
                continue
            results.extend(
                self.client.propagate_notifications(fhir_content, owner_subscribers)
            )
        return self._handle_notification_results(results)

    def _authorize_subscribers(
        self,
        imis_resource: Union[HistoryModel, VersionedModel],
        subscribers: List[Subscription],
    ) -> Tuple[List[Subscription], List[SubscriberNotificationOutput]]:
        """
        Keep the subscriptions whose owner may read this very instance now.

        A subscription only states what its owner wanted to follow; whether they may
        still read it is decided per notification: the owner may have been deleted
        or lost the right since, and row scope is a property of the instance.
        """
        authorized = []
        refused = []
        for subscriber in subscribers:
            reason = notification_refusal(subscriber.user_created, imis_resource)
            if reason is None:
                authorized.append(subscriber)
            else:
                refused.append(
                    SubscriberNotificationOutput(
                        subscriber, False, f"Not authorized, reason: {reason}"
                    )
                )
        return authorized, refused

    @staticmethod
    def _group_by_owner(subscribers: List[Subscription]):
        groups = {}
        for subscriber in subscribers:
            owner = subscriber.user_created
            groups.setdefault(owner.id, (owner, []))[1].append(subscriber)
        return list(groups.values())

    def _validate_subscribers(
        self, subscribers: List[Subscription]
    ) -> Tuple[List[Subscription], List[SubscriberNotificationOutput]]:
        url_validator = URLValidator()
        valid_subscribers = []
        rejected = []
        for subscriber in subscribers:
            try:
                url_validator(subscriber.endpoint)
                if subscriber.channel != Subscription.SubscriptionChannel.REST_HOOK:
                    raise ValidationError(
                        f"Subscriber {subscriber} not eligible for REST notification. "
                        f"Subscriber eligible for channel {subscriber.channel}."
                    )
                valid_subscribers.append(subscriber)

            except ValidationError as e:
                rejected.append(
                    SubscriberNotificationOutput(
                        subscriber, False, f"Validation not passed, reason: {e}"
                    )
                )
        return valid_subscribers, rejected

    def _resource_to_fhir(
        self, imis_resource: Union[HistoryModel, VersionedModel], owner
    ) -> dict:
        """
        The resource as `owner` would read it.

        Converters work on the current user (`BaseFHIRConverter.__init__` sets it), so
        the conversion runs as the owner and the user who made the change is put
        back afterwards.
        """
        previous_user = get_current_user()
        try:
            converter = self.converter_class(user=owner)
            return converter.to_fhir_obj(
                imis_resource, ReferenceConverterMixin.UUID_REFERENCE_TYPE
            ).dict()
        finally:
            if previous_user is not None:
                set_current_user(previous_user)
            else:
                clear_current_user()

    def _handle_notification_results(
        self, notification_result: Iterable[SubscriberNotificationOutput]
    ) -> Iterable[SubscriptionNotificationResult]:
        return [self.__save_result_in_db(result) for result in notification_result]

    def __save_result_in_db(self, result: SubscriberNotificationOutput):
        new_entry = SubscriptionNotificationResult(
            subscription=result.subscription,
            error=str(result.reason_of_failure) if result.reason_of_failure else None,
            notified_successfully=result.notification_success,
            notification_time=core.datetimes.ad_datetime.AdDatetime.now(),
        )
        new_entry.save()
        return new_entry
