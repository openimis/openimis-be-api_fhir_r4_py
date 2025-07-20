from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClaimResponseViewSet

router = DefaultRouter()
router.register(r'ClaimResponse', ClaimResponseViewSet, basename='ClaimResponse_R4')

urlpatterns = [
    path('', include(router.urls)),
]
