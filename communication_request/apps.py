from django.apps import AppConfig


class CommunicationRequestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communication_request'
    verbose_name = 'FHIR CommunicationRequest Resource'
    
    def ready(self):
        """
        Initialize the CommunicationRequest FHIR resource app
        """
        pass
