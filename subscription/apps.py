from django.apps import AppConfig


class subscriptionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscription'
    verbose_name = 'FHIR subscription Resource'
    
    def ready(self):
        """
        Initialize the subscription FHIR resource app
        """
        pass
