from django.apps import AppConfig


class coverageeligibilityrequestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'coverage_eligibility_request'
    verbose_name = 'FHIR coverageeligibilityrequest Resource'
    
    def ready(self):
        """
        Initialize the coverageeligibilityrequest FHIR resource app
        """
        pass
