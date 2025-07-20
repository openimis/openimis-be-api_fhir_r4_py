from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContractViewSet

router = DefaultRouter()
router.register(r'Contract', ContractViewSet, basename='Contract_R4')

urlpatterns = [
    path('', include(router.urls)),
]
