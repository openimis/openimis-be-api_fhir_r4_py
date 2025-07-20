from django.apps import AppConfig


class LocationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'location'
    verbose_name = 'FHIR Location Resource'
    
    def ready(self):
        """
        Initialize the Location FHIR resource app
        """
        pass