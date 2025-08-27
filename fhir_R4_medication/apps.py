from django.apps import AppConfig


class MedicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medication'
    verbose_name = 'FHIR Medication Resource'
    
    def ready(self):
        """
        Initialize the Medication FHIR resource app
        """
        pass