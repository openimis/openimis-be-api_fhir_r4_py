from rest_framework.viewsets import GenericViewSet

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin, ListModelMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiCommunicationRequestPermissions
from fhir_R4_Communication.serializers.communicationRequestSerializer import CommunicationRequestSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from claim.models import Claim


class CommunicationRequestViewSet(
    BaseFHIRView,
    MultiIdentifierRetrieverMixin,
    ListModelMixin,
    GenericViewSet
):
    retrievers = [UUIDIdentifierModelRetriever]
    serializer_class = CommunicationRequestSerializer
    permission_classes = (FHIRApiCommunicationRequestPermissions,)

    def get_queryset(self):
        # Use a simpler queryset to avoid ClaimAdmin table dependency
        queryset = Claim.objects.filter(
            feedback_status__in=[
                Claim.FEEDBACK_SELECTED, Claim.FEEDBACK_DELIVERED, Claim.FEEDBACK_BYPASSED
            ],
            validity_to__isnull=True
        ).order_by('validity_from')
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
