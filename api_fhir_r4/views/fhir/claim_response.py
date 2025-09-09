from rest_framework.viewsets import GenericViewSet

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin, ListModelMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiClaimPermissions
from api_fhir_r4.serializers import ClaimResponseSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from claim.models import Claim


class ClaimResponseViewSet(
    BaseFHIRView,
    ListModelMixin,
    MultiIdentifierRetrieverMixin,
    GenericViewSet
):
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializer_class = ClaimResponseSerializer
    permission_classes = (FHIRApiClaimPermissions,)

    def get_queryset(self):
        # Use a simpler queryset to avoid ClaimAdmin table dependency
        queryset = Claim.objects.filter(validity_to__isnull=True).order_by('validity_from')
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
