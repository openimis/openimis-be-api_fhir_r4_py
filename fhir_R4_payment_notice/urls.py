from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentNoticeViewSet

router = DefaultRouter()
router.register(r'PaymentNotice', PaymentNoticeViewSet, basename='PaymentNotice_R4')

urlpatterns = [
    path('', include(router.urls)),
]
