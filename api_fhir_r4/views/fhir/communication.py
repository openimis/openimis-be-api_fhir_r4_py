from rest_framework import viewsets

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiCommunicationRequestPermissions
from api_fhir_r4.serializers import CommunicationSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from claim.models import Feedback


class CommunicationViewSet(BaseFHIRView, MultiIdentifierRetrieverMixin, viewsets.ModelViewSet):
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializer_class = CommunicationSerializer
    permission_classes = (FHIRApiCommunicationRequestPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("identifier")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            queryset = queryset.filter(validity_to__isnull=True)
        serializer = CommunicationSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, *args, **kwargs):
        response = super().retrieve(self, *args, **kwargs)
        return response

    def get_queryset(self):
        queryset = Feedback.objects.filter(validity_to=None).order_by('validity_from')
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
