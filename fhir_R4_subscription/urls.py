from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.subscriptionViewSet import SubscriptionViewSet

router = DefaultRouter()
router.register(r'Subscription', SubscriptionViewSet, basename='Subscription_R4')

urlpatterns = [
    path('', include(router.urls)),
]
