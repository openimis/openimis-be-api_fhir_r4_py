from django.apps import AppConfig


class communicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communication'
    verbose_name = 'FHIR communication Resource'
    
    def ready(self):
        """
        Initialize the communication FHIR resource app
        """
        pass
