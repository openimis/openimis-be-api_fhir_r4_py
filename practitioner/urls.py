from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PractitionerViewSet

router = DefaultRouter()
router.register(r'Practitioner', PractitionerViewSet, basename='Practitioner_R4')

urlpatterns = [
    path('', include(router.urls)),
]
