from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet

router = DefaultRouter()
router.register(r'Patient', PatientViewSet, basename='Patient_R4')

urlpatterns = [
    path('', include(router.urls)),
]
