from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CoverageViewSet

router = DefaultRouter()
router.register(r'Coverage', CoverageViewSet, basename='Coverage_R4')

urlpatterns = [
    path('', include(router.urls)),
]
