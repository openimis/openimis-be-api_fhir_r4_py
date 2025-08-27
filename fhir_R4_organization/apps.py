from django.apps import AppConfig


class OrganizationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organization'
    verbose_name = 'FHIR Organization Resource'
    
    def ready(self):
        """
        Initialize the Organization FHIR resource app
        """
        pass