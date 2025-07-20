from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet

router = DefaultRouter()
router.register(r'Group', GroupViewSet, basename='Group_R4')

urlpatterns = [
    path('', include(router.urls)),
]
