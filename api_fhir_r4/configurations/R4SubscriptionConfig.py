from api_fhir_r4.configurations import SubscriptionConfiguration


class R4SubscriptionConfig(SubscriptionConfiguration):
    _config = "R4_fhir_subscription_config"

    @classmethod
    def build_configuration(cls, cfg):
        cls.get_config().R4_fhir_subscription_config = cfg[
            "R4_fhir_subscription_config"
        ]

    @classmethod
    def get_fhir_sub_search_perms(cls):
        # The AppConfig constant, no longer the config: a right is not overridden.
        from django.apps import apps as django_apps

        return django_apps.get_app_config("api_fhir_r4").fhir_sub_search_perms

    @classmethod
    def get_fhir_sub_create_perms(cls):
        # The AppConfig constant, no longer the config: a right is not overridden.
        from django.apps import apps as django_apps

        return django_apps.get_app_config("api_fhir_r4").fhir_sub_create_perms

    @classmethod
    def get_fhir_sub_update_perms(cls):
        # The AppConfig constant, no longer the config: a right is not overridden.
        from django.apps import apps as django_apps

        return django_apps.get_app_config("api_fhir_r4").fhir_sub_update_perms

    @classmethod
    def get_fhir_sub_delete_perms(cls):
        # The AppConfig constant, no longer the config: a right is not overridden.
        from django.apps import apps as django_apps

        return django_apps.get_app_config("api_fhir_r4").fhir_sub_delete_perms

    @classmethod
    def get_fhir_subscription_channel_rest_hook(cls):
        return cls.get_config_attribute("R4_fhir_subscription_config").get(
            "fhir_sub_channel_rest_hook", "rest_hook"
        )

    @classmethod
    def get_fhir_subscription_status_off(cls):
        return cls.get_config_attribute("R4_fhir_subscription_config").get(
            "fhir_sub_status_off", "off"
        )

    @classmethod
    def get_fhir_subscription_status_active(cls):
        return cls.get_config_attribute("R4_fhir_subscription_config").get(
            "fhir_sub_status_active", "active"
        )

    @classmethod
    def get_fhir_sub_criteria_key_resource(cls):
        return cls.get_config_attribute("R4_fhir_subscription_config").get(
            "get_fhir_sub_criteria_key_resource", "resource"
        )

    @classmethod
    def get_fhir_sub_criteria_key_resource_type(cls):
        return cls.get_config_attribute("R4_fhir_subscription_config").get(
            "get_fhir_sub_criteria_key_resource_type", "resource_type"
        )
