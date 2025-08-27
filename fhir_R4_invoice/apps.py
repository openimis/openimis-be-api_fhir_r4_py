from django.apps import AppConfig


class invoiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoice'
    verbose_name = 'FHIR invoice Resource'
    
    def ready(self):
        """
        Initialize the invoice FHIR resource app
        """
        pass
