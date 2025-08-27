from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InsurancePlanViewSet

router = DefaultRouter()
router.register(r'InsurancePlan', InsurancePlanViewSet, basename='InsurancePlan_R4')

urlpatterns = [
    path('', include(router.urls)),
]
