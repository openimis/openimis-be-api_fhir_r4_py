from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommunicationRequestViewSet

router = DefaultRouter()
router.register(r'CommunicationRequest', CommunicationRequestViewSet, basename='CommunicationRequest_R4')

urlpatterns = [
    path('', include(router.urls)),
]
