from rest_framework import viewsets

from product.models import Product
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever

from ..serializers.insurancePlanSerializer import InsurancePlanSerializer, InsurancePlanSerializerSchema
from ..permissions.insurancePermissions import FHIRApiInsurancePlanPermissions


class InsurancePlanViewSet(BaseFHIRView, MultiIdentifierRetrieverMixin, viewsets.ReadOnlyModelViewSet):
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializer_class = InsurancePlanSerializer
    permission_classes = (FHIRApiInsurancePlanPermissions,)
    http_method_names = ("get",)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("identifier")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            queryset = queryset.filter(validity_to__isnull=True)
        serializer = InsurancePlanSerializer(self.paginate_queryset(queryset), many=True, user=request.user)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Product.objects.all().order_by('validity_from')
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)


