from rest_framework import viewsets

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin, MultiIdentifierUpdateMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, GroupIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiGroupPermissions
from api_fhir_r4.serializers import GroupSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from insuree.models import Family


class GroupViewSet(BaseFHIRView, MultiIdentifierRetrieverMixin,
                   MultiIdentifierUpdateMixin, viewsets.ModelViewSet):
    retrievers = [UUIDIdentifierModelRetriever, GroupIdentifierModelRetriever]
    serializer_class = GroupSerializer
    permission_classes = (FHIRApiGroupPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("identifier")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            queryset = queryset.filter(validity_to__isnull=True)
        serializer = GroupSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, *args, **kwargs):
        response = super().retrieve(self, *args, **kwargs)
        return response

    def get_queryset(self):
        queryset = Family.objects.all().order_by('validity_from')
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
