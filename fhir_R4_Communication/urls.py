from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.communicationViewSet import CommunicationViewSet
from .views.communicationRequestViewSet import CommunicationRequestViewSet

router = DefaultRouter()
router.register(r'Communication', CommunicationViewSet, basename='Communication_R4')
router.register(r'CommunicationRequest', CommunicationRequestViewSet, basename='CommunicationRequest_R4')

urlpatterns = [
    path('', include(router.urls)),
]
