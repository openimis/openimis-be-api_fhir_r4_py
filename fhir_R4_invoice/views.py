from rest_framework import viewsets

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiInvoicePermissions
from api_fhir_r4.serializers import InvoiceSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from invoice.models import Bill
from core.utils import filter_validity
import logging

logger = logging.getLogger(__name__)


class InvoiceViewSet(
    BaseFHIRView,
    MultiIdentifierRetrieverMixin,
    viewsets.ModelViewSet
):
    """
    FHIR Invoice Resource ViewSet
    Maps openIMIS Bill to FHIR Invoice resource
    """
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializer_class = InvoiceSerializer
    permission_classes = (FHIRApiInvoicePermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("identifier")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            queryset = queryset.filter(*filter_validity())
        serializer = InvoiceSerializer(self.paginate_queryset(queryset), many=True, user=request.user)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        queryset = Bill.get_queryset(None, self.request.user)
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
