from django.apps import AppConfig


class paymentnoticeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payment_notice'
    verbose_name = 'FHIR paymentnotice Resource'
    
    def ready(self):
        """
        Initialize the paymentnotice FHIR resource app
        """
        pass
