import datetime
 
from rest_framework.viewsets import GenericViewSet
from api_fhir_r4.mixins import ListModelMixin, RetrieveModelMixin
from api_fhir_r4.permissions import FHIRApiCoverageRequestPermissions
from api_fhir_r4.serializers.coverageSerializer import CoverageSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from policy.models import Policy


class CoverageRequestQuerySet(BaseFHIRView, RetrieveModelMixin, ListModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    serializer_class = CoverageSerializer
    permission_classes = (FHIRApiCoverageRequestPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset.prefetch_related('services')
        refDate = request.GET.get('refDate')
        refEndDate = request.GET.get('refEndDate')
        identifier = request.GET.get("identifier")
        if identifier:
            queryset = queryset.filter(chf_id=identifier)
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from')
            if refDate != None:
                isValidDate = True
                try:
                    datevar = datetime.datetime.strptime(refDate, "%Y-%m-%d").date()
                except ValueError:
                    isValidDate = False
                queryset = queryset.filter(validity_from__gte=datevar)
            if refEndDate != None:
                isValidDate = True
                try:
                    datevar = datetime.datetime.strptime(refEndDate, "%Y-%m-%d").date()
                except ValueError:
                    isValidDate = False
                queryset = queryset.filter(validity_from__lt=datevar)

        serializer = CoverageSerializer(self.paginate_queryset(queryset), many=True, user=request.user)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        queryset = Policy.get_queryset(None, self.request.user)
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
