import datetime

from django.db.models import Prefetch
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import GenericViewSet

from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin, ListModelMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiClaimPermissions
from api_fhir_r4.serializers import ClaimSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from claim.models import Claim, ClaimItem, ClaimService
from insuree.models import Insuree, InsureePolicy


class ClaimViewSet(BaseFHIRView, MultiIdentifierRetrieverMixin, ListModelMixin, GenericViewSet):
    """
    FHIR Claim Resource ViewSet
    Maps openIMIS Claim to FHIR Claim resource
    """
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializer_class = ClaimSerializer
    permission_classes = (FHIRApiClaimPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        refDate = request.GET.get('refDate')
        identifier = request.GET.get("identifier")
        patient = request.GET.get("patient")
        contained = bool(request.GET.get("contained"))

        if identifier is not None:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from')
            if refDate is not None:
                try:
                    date_from = datetime.datetime.strptime(refDate, "%Y-%m-%d").date()
                    queryset = queryset.filter(validity_from__gte=date_from)
                except ValueError as v:
                    raise ValidationError({'refDate': 'Invalid date format, should be in "%Y-%m-%d" format'})

            if patient is not None:
                for_patient = Insuree.objects.get(uuid=patient)
                queryset = queryset.filter(insuree=for_patient)

        serializer = ClaimSerializer(self.paginate_queryset(queryset), many=True, context={'contained': contained}, user=request.user)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        contained = bool(request.GET.get("contained"))
        ref_type, instance = self._get_object_with_first_valid_retriever(kwargs['identifier'])
        serializer = ClaimSerializer(instance, context={'contained': contained}, user=request.user)
        return Response(serializer.data)

    def get_queryset(self):
        queryset = Claim.get_queryset(None, self.request.user) \
            .prefetch_related(Prefetch('items', queryset=ClaimItem.objects.select_related('item'))) \
            .prefetch_related(Prefetch('services', queryset=ClaimService.objects.select_related('service'))) \
            .select_related('insuree') \
            .select_related('health_facility') \
            .select_related('admin')

        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
