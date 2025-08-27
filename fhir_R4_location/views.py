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
    """
    FHIR Location Resource ViewSet
    Maps openIMIS Location to FHIR Location resource
    """
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
            serializer = LocationSiteSerializer(self.paginate_queryset(queryset), many=True, user=request.user)
        else:
            serializer = LocationSerializer(self.paginate_queryset(queryset), many=True, user=request.user)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self, physical_type=None):
        if physical_type and physical_type == 'si':
            queryset = HealthFacility.get_queryset(None, self.request.user)
        else:
            queryset = Location.get_queryset(None, self.request.user)
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
