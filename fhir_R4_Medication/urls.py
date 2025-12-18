from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.medicationViewSet import MedicationViewSet

router = DefaultRouter()
router.register(r'Medication', MedicationViewSet, basename='Medication_R4')

urlpatterns = [
    path('', include(router.urls)),
]


