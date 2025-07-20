from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClaimViewSet

router = DefaultRouter()
router.register(r'Claim', ClaimViewSet, basename='Claim_R4')

urlpatterns = [
    path('', include(router.urls)),
]
