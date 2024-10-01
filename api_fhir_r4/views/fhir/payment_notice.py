from rest_framework import viewsets

from api_fhir_r4.mixins import (
    MultiIdentifierRetrieverMixin,
    MultiIdentifierUpdateMixin
)
from api_fhir_r4.model_retrievers import (
    UUIDIdentifierModelRetriever,
    GroupIdentifierModelRetriever
)
from api_fhir_r4.paymentNotice import PaymentNoticeSerializer
from api_fhir_r4.permissions import FHIRApiPaymentPermissions
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import DateUpdatedRequestParameterFilter
from invoice.models import PaymentInvoice


class PaymentNoticeViewSet(
    BaseFHIRView,
    MultiIdentifierRetrieverMixin,
    MultiIdentifierUpdateMixin,
    viewsets.ModelViewSet
):
    retrievers = [UUIDIdentifierModelRetriever, GroupIdentifierModelRetriever]
    serializer_class = PaymentNoticeSerializer
    permission_classes = (FHIRApiPaymentPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("identifier")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            queryset = queryset.filter(is_deleted=False)
        serializer = PaymentNoticeSerializer(self.paginate_queryset(queryset), many=True, user=request.user)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, *args, **kwargs):
        response = super().retrieve(self, *args, **kwargs)
        return response

    def get_queryset(self):
        queryset = PaymentInvoice.objects.filter(is_deleted=False).order_by('date_created')
        return DateUpdatedRequestParameterFilter(self.request).filter_queryset(queryset)
