from typing import Union

from django.db.models import Q

from api_fhir_r4.configurations import R4SubscriptionConfig
from api_fhir_r4.models import Subscription
from core.datetimes.ad_datetime import datetime
from core.models import HistoryModel, VersionedModel


class SubscriptionCriteriaFilter:
    def __init__(self, imis_resource: Union[HistoryModel, VersionedModel], fhir_resource_name: str,
                 fhir_resource_type_name: str):
        self.fhir_resource_name = fhir_resource_name
        self.fhir_resource_type_name = fhir_resource_type_name
        self.imis_resource = imis_resource

    def get_filtered_subscriptions(self):
        subscriptions = self._get_all_active_subscriptions()
        return self._get_matching_subscriptions(subscriptions)

    def _get_all_active_subscriptions(self):
        queryset = Subscription.objects.filter(status=Subscription.SubscriptionStatus.ACTIVE.value,
                                               expiring__gt=datetime.now(), is_deleted=False)
        if self.fhir_resource_name:
            queryset = queryset.filter(criteria__jsoncontains={
                R4SubscriptionConfig.get_fhir_sub_criteria_key_resource(): self.fhir_resource_name})
        if self.fhir_resource_type_name:
            queryset = queryset.filter(
                ~Q(criteria__jsoncontainskey=R4SubscriptionConfig.get_fhir_sub_criteria_key_resource_type() )| Q(
                    criteria__jsoncontains={
                        R4SubscriptionConfig.get_fhir_sub_criteria_key_resource_type(): self.fhir_resource_type_name}))
        return queryset.all()

    def _get_matching_subscriptions(self, subscriptions):
        return [subscription for subscription in subscriptions
                if self._is_matching_subscription(subscription)]

    def _is_matching_subscription(self, sub):
        criteria = {criteria: sub.criteria[criteria] for criteria in sub.criteria if
                    criteria != R4SubscriptionConfig.get_fhir_sub_criteria_key_resource()
                    and criteria != R4SubscriptionConfig.get_fhir_sub_criteria_key_resource_type()}
        return not criteria or self._is_resource_matching_criteria(criteria)

    def _is_resource_matching_criteria(self, criteria):
        criteria['uuid'] = self.imis_resource.uuid
        return type(self.imis_resource).objects.filter(**criteria).exists()
