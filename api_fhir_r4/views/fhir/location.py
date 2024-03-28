from rest_framework import viewsets

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin, MultiIdentifierUpdateMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiLocationPermissions
from api_fhir_r4.serializers import LocationSerializer, LocationSiteSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from location.models import HealthFacility, Location


class LocationViewSet(BaseFHIRView, MultiIdentifierRetrieverMixin,
                      viewsets.ModelViewSet, MultiIdentifierUpdateMixin):
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializer_class = LocationSerializer
    permission_classes = (FHIRApiLocationPermissions,)

    def list(self, request, *args, **kwargs):
        identifier = request.GET.get("identifier")
        physical_type = request.GET.get('physicalType')
        queryset = self.get_queryset(physical_type)
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from')
        if physical_type and physical_type == 'si':
            self.serializer_class = LocationSiteSerializer
            serializer = LocationSiteSerializer(self.paginate_queryset(queryset), many=True)
        else:
            serializer = LocationSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, *args, **kwargs):
        physical_type = self.request.GET.get('physicalType')
        if physical_type and physical_type == 'si':
            self.serializer_class = LocationSiteSerializer
            self.queryset = self.get_queryset('si')
        response = super().retrieve(self, *args, **kwargs)
        return response

    def get_queryset(self, physicalType='area'):
        if physicalType == 'si':
            hf_queryset = HealthFacility.get_queryset(None, self.request.user)
            queryset = hf_queryset.select_related('location').select_related('sub_level').select_related('legal_form')
        else:
            queryset = Location.get_queryset(None, self.request.user)
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
