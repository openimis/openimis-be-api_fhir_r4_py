from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommunicationViewSet

router = DefaultRouter()
router.register(r'Communication', CommunicationViewSet, basename='Communication_R4')

urlpatterns = [
    path('', include(router.urls)),
]
