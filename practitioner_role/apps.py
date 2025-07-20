from django.apps import AppConfig


class practitionerroleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'practitioner_role'
    verbose_name = 'FHIR practitionerrole Resource'
    
    def ready(self):
        """
        Initialize the practitionerrole FHIR resource app
        """
        pass
