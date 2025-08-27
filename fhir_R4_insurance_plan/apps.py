from django.apps import AppConfig


class insuranceplanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'insurance_plan'
    verbose_name = 'FHIR insuranceplan Resource'
    
    def ready(self):
        """
        Initialize the insuranceplan FHIR resource app
        """
        pass
