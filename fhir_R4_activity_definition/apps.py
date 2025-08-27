from django.apps import AppConfig


class activitydefinitionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity_definition'
    verbose_name = 'FHIR activitydefinition Resource'
    
    def ready(self):
        """
        Initialize the activitydefinition FHIR resource app
        """
        pass
