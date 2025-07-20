from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationViewSet

router = DefaultRouter()
router.register(r'Location', LocationViewSet, basename='Location_R4')

urlpatterns = [
    path('', include(router.urls)),
]
