from django.apps import AppConfig


class CoverageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'coverage'
    verbose_name = 'FHIR Coverage Resource'
    
    def ready(self):
        """
        Initialize the Coverage FHIR resource app
        """
        pass
