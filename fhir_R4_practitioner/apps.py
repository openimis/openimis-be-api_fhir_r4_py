from django.apps import AppConfig


class PractitionerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'practitioner'
    verbose_name = 'FHIR Practitioner Resource'
    
    def ready(self):
        """
        Initialize the Practitioner FHIR resource app
        """
        pass