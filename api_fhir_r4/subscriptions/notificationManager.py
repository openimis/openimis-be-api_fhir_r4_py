
from typing import Union, List, Tuple, Iterable

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

import core.datetimes.ad_datetime
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.models import Subscription, SubscriptionNotificationResult
from api_fhir_r4.subscriptions.notificationClient import RestSubscriptionNotificationClient, \
    SubscriberNotificationOutput
from core.models import HistoryModel, VersionedModel


class RestSubscriptionNotificationManager:

    def __init__(self,  fhir_converter: BaseFHIRConverter,
                 client: RestSubscriptionNotificationClient = None):
        if client is None:
            client = RestSubscriptionNotificationClient()
        self.client = client
        self.fhir_converter = fhir_converter

    def notify_subscribers_with_resource(
            self, imis_resource: Union[HistoryModel, VersionedModel], subscribers: List[Subscription])\
            -> Iterable[SubscriptionNotificationResult]:
        fhir_content = self._resource_to_fhir(imis_resource)
        valid, rejected = self._validate_subscribers(subscribers)
        result = self.client.propagate_notifications(fhir_content, valid)
        combined_result = [*result, *rejected]
        return self._handle_notification_results(combined_result)

    def _validate_subscribers(self, subscribers: List[Subscription]) \
            -> Tuple[List[Subscription], List[SubscriberNotificationOutput]]:
        url_validator = URLValidator()
        valid_subscribers = []
        rejected = []
        for subscriber in subscribers:
            try:
                url_validator(subscriber.endpoint)
                if subscriber.channel != Subscription.SubscriptionChannel.REST_HOOK:
                    raise ValidationError(f'Subscriber {subscriber} not eligible for REST notification. '
                                          f'Subscriber eligible for channel {subscriber.channel}.')
                valid_subscribers.append(subscriber)

            except ValidationError as e:
                rejected.append(
                    SubscriberNotificationOutput(
                        subscriber, False, F'Validation not passed, reason: {e}')
                )
        return valid_subscribers, rejected

    def _resource_to_fhir(self, imis_resource: Union[HistoryModel, VersionedModel]) -> dict:
        return self.fhir_converter.to_fhir_obj(imis_resource, ReferenceConverterMixin.UUID_REFERENCE_TYPE).dict()

    def _handle_notification_results(self, notification_result: Iterable[SubscriberNotificationOutput])\
            -> Iterable[SubscriptionNotificationResult]:
        return [self.__save_result_in_db(result) for result in notification_result]

    def __save_result_in_db(self, result: SubscriberNotificationOutput):
        new_entry = SubscriptionNotificationResult(
            subscription=result.subscription,
            error=str(result.reason_of_failure) if result.reason_of_failure else None,
            notified_successfully=result.notification_success,
            notification_time=core.datetimes.ad_datetime.AdDatetime.now()
        )
        new_entry.save()
        return new_entry

