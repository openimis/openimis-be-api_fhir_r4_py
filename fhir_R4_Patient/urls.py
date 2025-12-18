from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.insureeViewSet import (
    InsureeViewSet,
    CodeSystemOpenIMISPatientEducationLevelViewSet,
    CodeSystemOpenIMISPatientProfessionViewSet,
    CodeSystemOpenIMISPatientIdentificationTypeViewSet,
    CodeSystemOpenIMISPatientRelationshipViewSet,
)


router = DefaultRouter()
router.register(r'Patient', InsureeViewSet, basename='Patient_R4')
router.register(r'CodeSystem/patient-education-level', CodeSystemOpenIMISPatientEducationLevelViewSet, basename='CodeSystem/patient-education-level_R4')
router.register(r'CodeSystem/patient-profession', CodeSystemOpenIMISPatientProfessionViewSet, basename='CodeSystem/patient-profession_R4')
router.register(r'CodeSystem/patient-identification-type', CodeSystemOpenIMISPatientIdentificationTypeViewSet, basename='CodeSystem/patient-identification-type_R4')
router.register(r'CodeSystem/patient-contact-relationship', CodeSystemOpenIMISPatientRelationshipViewSet, basename='CodeSystem/patient-contact-relationship_R4')


urlpatterns = [
    path('', include(router.urls)),
]



