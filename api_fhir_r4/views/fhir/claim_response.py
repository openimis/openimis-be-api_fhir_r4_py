from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiClaimPermissions
from api_fhir_r4.serializers import ClaimResponseSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from claim.models import Claim


class ClaimResponseViewSet(BaseFHIRView, MultiIdentifierRetrieverMixin, mixins.ListModelMixin, GenericViewSet,
                           mixins.UpdateModelMixin):
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializer_class = ClaimResponseSerializer
    permission_classes = (FHIRApiClaimPermissions,)

    def get_queryset(self):
        queryset = Claim.get_queryset(None, self.request.user).order_by('validity_from')
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
