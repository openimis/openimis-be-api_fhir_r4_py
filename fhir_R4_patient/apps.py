from django.apps import AppConfig


class PatientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'patient'
    verbose_name = 'FHIR Patient Resource'
    
    def ready(self):
        """
        Initialize the Patient FHIR resource app
        """
        pass
