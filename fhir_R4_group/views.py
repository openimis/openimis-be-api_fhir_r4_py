from rest_framework import viewsets

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiInsureePermissions
from api_fhir_r4.serializers import GroupSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from insuree.models import Family
from core.utils import filter_validity
import logging

logger = logging.getLogger(__name__)


class GroupViewSet(
    BaseFHIRView,
    MultiIdentifierRetrieverMixin,
    viewsets.ModelViewSet
):
    """
    FHIR Group Resource ViewSet
    Maps openIMIS Family to FHIR Group resource
    """
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializer_class = GroupSerializer
    permission_classes = (FHIRApiInsureePermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("identifier")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            queryset = queryset.filter(*filter_validity())
        serializer = GroupSerializer(self.paginate_queryset(queryset), many=True, user=request.user)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        queryset = Family.get_queryset(None, self.request.user)
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
