from rest_framework.request import Request
from django.utils.functional import cached_property

from api_fhir_r4.mapping.invoiceMapping import InvoiceTypeMapping, BillTypeMapping
from api_fhir_r4.mixins import (
    MultiIdentifierRetrieveManySerializersMixin,
    MultiIdentifierRetrieverMixin
)
from api_fhir_r4.model_retrievers import (
    CodeIdentifierModelRetriever,
    DatabaseIdentifierModelRetriever,
    UUIDIdentifierModelRetriever
)
from api_fhir_r4.multiserializer import modelViewset
from api_fhir_r4.permissions import (
    FHIRApiInvoicePermissions,
    FHIRApiBillPermissions
)
from api_fhir_r4.serializers import (
    InvoiceSerializer,
    BillSerializer
)
from api_fhir_r4.views.fhir.base import BaseMultiserializerFHIRView
from api_fhir_r4.views.filters import DateUpdatedRequestParameterFilter
from invoice.models import Bill
from invoice.models import Invoice


class InvoiceViewSet(BaseMultiserializerFHIRView,
                     modelViewset.MultiSerializerModelViewSet,
                     MultiIdentifierRetrieveManySerializersMixin, MultiIdentifierRetrieverMixin):
    retrievers = [UUIDIdentifierModelRetriever, DatabaseIdentifierModelRetriever, CodeIdentifierModelRetriever]
    lookup_field = 'identifier'

    @cached_property
    def serializers(self):
        return {
            InvoiceSerializer:
                (self._invoice_queryset(), self._invoice_serializer_validator, (FHIRApiInvoicePermissions,)),
            BillSerializer:
                (self._bill_queryset(), self._bill_serializer_validator, (FHIRApiBillPermissions,))
        }

    @classmethod
    def _invoice_serializer_validator(cls, context):
        return cls._base_request_validator_dispatcher(
            request=context['request'],
            get_check=lambda x: cls._get_type_from_query(x) in ('invoice', None),
            post_check=lambda x: cls._get_type_from_body(x) in [item['code'] for item in
                                                                InvoiceTypeMapping.invoice_type],
            put_check=lambda x: cls._get_type_from_body(x) in [item['code'] for item in
                                                               InvoiceTypeMapping.invoice_type],
        )

    @classmethod
    def _bill_serializer_validator(cls, context):
        return cls._base_request_validator_dispatcher(
            request=context['request'],
            get_check=lambda x: cls._get_type_from_query(x) in ('bill', None),
            post_check=lambda x: cls._get_type_from_body(x) in [item['code'] for item in BillTypeMapping.invoice_type],
            put_check=lambda x: cls._get_type_from_body(x) in [item['code'] for item in BillTypeMapping.invoice_type],
        )

    @classmethod
    def _base_request_validator_dispatcher(cls, request: Request, get_check, post_check, put_check):
        if request.method == 'GET':
            return get_check(request)
        elif request.method == 'POST':
            return post_check(request)
        elif request.method == 'PUT':
            return put_check(request)
        return True

    def list(self, request, *args, **kwargs):
        identifier = request.GET.get("code")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Invoice.objects

    def _invoice_queryset(self):
        queryset = Invoice.objects.filter(is_deleted=False).order_by('date_created')
        return DateUpdatedRequestParameterFilter(self.request).filter_queryset(queryset)

    def _bill_queryset(self):
        queryset = Bill.objects.filter(is_deleted=False).order_by('date_created')
        return DateUpdatedRequestParameterFilter(self.request).filter_queryset(queryset)

    @classmethod
    def _get_type_from_body(cls, request):
        try:
            return request.data['type'][0]['coding'][0]['code'].lower()
        except KeyError:
            return None

    @classmethod
    def _get_type_from_query(cls, request):
        try:
            return request.GET['resourceType'].lower()
        except KeyError:
            return None
