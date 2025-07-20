from rest_framework import viewsets

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiClaimAdminPractitionerRolePermissions
from api_fhir_r4.serializers import ClaimAdminPractitionerRoleSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from claim.models import ClaimAdmin
from core.utils import filter_validity
import logging

logger = logging.getLogger(__name__)


class PractitionerRoleViewSet(
    BaseFHIRView,
    MultiIdentifierRetrieverMixin,
    viewsets.ModelViewSet
):
    """
    FHIR PractitionerRole Resource ViewSet
    Maps openIMIS ClaimAdmin to FHIR PractitionerRole resource
    """
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializer_class = ClaimAdminPractitionerRoleSerializer
    permission_classes = (FHIRApiClaimAdminPractitionerRolePermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("identifier")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            queryset = queryset.filter(*filter_validity())
        serializer = ClaimAdminPractitionerRoleSerializer(self.paginate_queryset(queryset), many=True, user=request.user)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        queryset = ClaimAdmin.get_queryset(None, self.request.user)
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
