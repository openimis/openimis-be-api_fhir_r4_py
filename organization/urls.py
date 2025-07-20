from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet

router = DefaultRouter()
router.register(r'Organization', OrganizationViewSet, basename='Organization_R4')

urlpatterns = [
    path('', include(router.urls)),
]
