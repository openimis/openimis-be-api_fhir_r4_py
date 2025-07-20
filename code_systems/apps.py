from django.apps import AppConfig


class codesystemsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'code_systems'
    verbose_name = 'FHIR codesystems Resource'
    
    def ready(self):
        """
        Initialize the codesystems FHIR resource app
        """
        pass
