from django.apps import AppConfig


class claimresponseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'claim_response'
    verbose_name = 'FHIR claimresponse Resource'
    
    def ready(self):
        """
        Initialize the claimresponse FHIR resource app
        """
        pass
