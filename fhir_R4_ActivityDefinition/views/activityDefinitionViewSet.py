from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin, ListModelMixin, AsyncOperationMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiActivityDefinitionPermissions
from fhir_R4_ActivityDefinition.serializers.activityDefinitionSerializer import ActivityDefinitionSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from medical.models import Service


class ActivityDefinitionViewSet(BaseFHIRView, MultiIdentifierRetrieverMixin, ListModelMixin, AsyncOperationMixin, GenericViewSet):
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializer_class = ActivityDefinitionSerializer
    permission_classes = (FHIRApiActivityDefinitionPermissions,)

    def get_queryset(self):
        queryset = Service.get_queryset(None, self.request.user)
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
    
    @action(detail=False, methods=['get'], url_path='async-list')
    def async_list(self, request, *args, **kwargs):
        """Async version of list operation for ActivityDefinition"""
        return super().async_list(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'], url_path='async')
    def async_retrieve(self, request, *args, **kwargs):
        """Async version of retrieve operation for ActivityDefinition"""
        return super().async_retrieve(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'], url_path='async-create')
    def async_create(self, request, *args, **kwargs):
        """Async version of create operation for ActivityDefinition"""
        return super().async_create(request, *args, **kwargs)
    
    @action(detail=True, methods=['put'], url_path='async')
    def async_update(self, request, *args, **kwargs):
        """Async version of update operation for ActivityDefinition"""
        return super().async_update(request, *args, **kwargs)
    
    @action(detail=True, methods=['patch'], url_path='async')
    def async_partial_update(self, request, *args, **kwargs):
        """Async version of partial_update operation for ActivityDefinition"""
        return super().async_partial_update(request, *args, **kwargs)
    
    @action(detail=True, methods=['delete'], url_path='async')
    def async_destroy(self, request, *args, **kwargs):
        """Async version of destroy operation for ActivityDefinition"""
        return super().async_destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], url_path='async-status/(?P<task_id>[^/.]+)')
    def async_status(self, request, task_id=None, *args, **kwargs):
        """Get the status of an async task"""
        return self.get_async_status(task_id)
    
    @action(detail=False, methods=['get'], url_path='async-result/(?P<task_id>[^/.]+)')
    def async_result(self, request, task_id=None, *args, **kwargs):
        """Get the result of a completed async task"""
        return self.get_async_result(task_id)
