from django.apps import AppConfig


class ClaimConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'claim'
    verbose_name = 'FHIR Claim Resource'
    
    def ready(self):
        """
        Initialize the Claim FHIR resource app
        """
        pass
