from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PractitionerRoleViewSet

router = DefaultRouter()
router.register(r'PractitionerRole', PractitionerRoleViewSet, basename='PractitionerRole_R4')

urlpatterns = [
    path('', include(router.urls)),
]
