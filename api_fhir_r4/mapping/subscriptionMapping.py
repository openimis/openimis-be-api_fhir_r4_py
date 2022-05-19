from api_fhir_r4.configurations import R4SubscriptionConfig
from api_fhir_r4.models import Subscription


class SubscriptionStatusMapping:
    _IMIS_OFF = Subscription.SubscriptionStatus.INACTIVE.value
    _FHIR_OFF = R4SubscriptionConfig.get_fhir_subscription_status_off()
    _IMIS_ACTIVE = Subscription.SubscriptionStatus.ACTIVE.value
    _FHIR_ACTIVE = R4SubscriptionConfig.get_fhir_subscription_status_active()

    to_fhir_status = {
        _IMIS_OFF: _FHIR_OFF,
        _IMIS_ACTIVE: _FHIR_ACTIVE
    }

    to_imis_status = {
        _FHIR_OFF: _IMIS_OFF,
        _FHIR_ACTIVE: _IMIS_ACTIVE
    }


class SubscriptionChannelMapping:
    _IMIS_REST_HOOK = Subscription.SubscriptionChannel.REST_HOOK.value
    _FHIR_REST_HOOK = R4SubscriptionConfig.get_fhir_subscription_channel_rest_hook()

    to_fhir_channel = {
        _IMIS_REST_HOOK: _FHIR_REST_HOOK
    }

    to_imis_channel = {
        _FHIR_REST_HOOK: _IMIS_REST_HOOK
    }
