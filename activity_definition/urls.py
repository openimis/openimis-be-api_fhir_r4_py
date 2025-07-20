from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityDefinitionViewSet

router = DefaultRouter()
router.register(r'ActivityDefinition', ActivityDefinitionViewSet, basename='ActivityDefinition_R4')

urlpatterns = [
    path('', include(router.urls)),
]
