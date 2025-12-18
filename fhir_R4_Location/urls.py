from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.locationViewSet import LocationViewSet, CodeSystemOrganizationHFLegalFormViewSet, CodeSystemOrganizationHFLevelViewSet

router = DefaultRouter()
router.register(r'Location', LocationViewSet, basename='Location_R4')
router.register(r'CodeSystem/organization-hf-legal-form', CodeSystemOrganizationHFLegalFormViewSet, basename='CodeSystem/organization-hf-legal-form_R4')
router.register(r'CodeSystem/organization-hf-level', CodeSystemOrganizationHFLevelViewSet, basename='CodeSystem/organization-hf-level_R4')

urlpatterns = [
    path('', include(router.urls)),
]


