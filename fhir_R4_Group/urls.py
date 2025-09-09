from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.groupViewSet import GroupViewSet
from .views.groupCodeSystems import (
    CodeSystemOpenIMISGroupTypeViewSet,
    CodeSystemOpenIMISGroupConfirmationTypeViewSet,
)


router = DefaultRouter()
router.register(r'Group', GroupViewSet, basename='Group_R4')
router.register(r'CodeSystem/group-type', CodeSystemOpenIMISGroupTypeViewSet, basename='CodeSystem/group-type_R4')
router.register(r'CodeSystem/group-confirmation-type', CodeSystemOpenIMISGroupConfirmationTypeViewSet, basename='CodeSystem/group-confirmation-type_R4')


urlpatterns = [
    path('', include(router.urls)),
]


