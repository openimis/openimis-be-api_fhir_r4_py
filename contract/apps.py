from django.apps import AppConfig


class ContractConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contract'
    verbose_name = 'FHIR Contract Resource'
    
    def ready(self):
        """
        Initialize the Contract FHIR resource app
        """
        pass
