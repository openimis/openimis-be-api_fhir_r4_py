from django.apps import AppConfig


class groupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'group'
    verbose_name = 'FHIR group Resource'
    
    def ready(self):
        """
        Initialize the group FHIR resource app
        """
        pass
