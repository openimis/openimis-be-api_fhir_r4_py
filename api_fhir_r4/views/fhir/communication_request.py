from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiCommunicationRequestPermissions
from api_fhir_r4.serializers import CommunicationRequestSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from claim.models import Claim


class CommunicationRequestViewSet(BaseFHIRView, MultiIdentifierRetrieverMixin, mixins.ListModelMixin, GenericViewSet):
    retrievers = [UUIDIdentifierModelRetriever]
    serializer_class = CommunicationRequestSerializer
    permission_classes = (FHIRApiCommunicationRequestPermissions,)

    def get_queryset(self):
        queryset = Claim.get_queryset(None, self.request.user).filter(feedback_status__in=[
            Claim.FEEDBACK_SELECTED, Claim.FEEDBACK_DELIVERED, Claim.FEEDBACK_BYPASSED
        ]).order_by('validity_from')
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
