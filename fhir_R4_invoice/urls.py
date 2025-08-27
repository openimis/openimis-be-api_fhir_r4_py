from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet

router = DefaultRouter()
router.register(r'Invoice', InvoiceViewSet, basename='Invoice_R4')

urlpatterns = [
    path('', include(router.urls)),
]
