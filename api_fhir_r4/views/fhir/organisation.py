from rest_framework.request import Request

from api_fhir_r4.mixins import MultiIdentifierRetrieveManySerializersMixin, MultiIdentifierRetrieverMixin
from api_fhir_r4.model_retrievers import CodeIdentifierModelRetriever, DatabaseIdentifierModelRetriever, \
    UUIDIdentifierModelRetriever
from api_fhir_r4.multiserializer import modelViewset
from api_fhir_r4.permissions import FHIRApiOrganizationPermissions
from api_fhir_r4.serializers import PolicyHolderOrganisationSerializer, HealthFacilityOrganisationSerializer
from api_fhir_r4.views.fhir.fhir_base_viewset import BaseMultiserializerFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter, DateUpdatedRequestParameterFilter
from location.models import HealthFacility
from policyholder.models import PolicyHolder


class OrganisationViewSet(BaseMultiserializerFHIRView,
                          modelViewset.MultiSerializerModelViewSet,
                          MultiIdentifierRetrieveManySerializersMixin, MultiIdentifierRetrieverMixin):
    retrievers = [UUIDIdentifierModelRetriever, DatabaseIdentifierModelRetriever, CodeIdentifierModelRetriever]
    permission_classes = (FHIRApiOrganizationPermissions,)

    lookup_field = 'identifier'

    @property
    def serializers(self):
        return {
            HealthFacilityOrganisationSerializer: (self._hf_queryset(), self._hf_serializer_validator),
            PolicyHolderOrganisationSerializer: (self._ph_queryset(), self._ph_serializer_validator),
        }

    @classmethod
    def _hf_serializer_validator(cls, context):
        return cls._base_request_validator_dispatcher(
            request=context['request'],
            get_check=lambda x: cls._get_type_from_query(x) in ('prov', None),
            post_check=lambda x: cls._get_type_from_body(x) == 'prov',
            put_check=lambda x: cls._get_type_from_body(x) in ('prov', None),
        )

    @classmethod
    def _ph_serializer_validator(cls, context):
        return cls._base_request_validator_dispatcher(
            request=context['request'],
            get_check=lambda x: cls._get_type_from_query(x) in ('bus', None),
            post_check=lambda x: cls._get_type_from_body(x) == 'bus',
            put_check=lambda x: cls._get_type_from_body(x) in ('bus', None),
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
        return HealthFacility.objects

    def _hf_queryset(self):
        queryset = HealthFacility.objects.filter(validity_to__isnull=True).order_by('validity_from')
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)

    def _ph_queryset(self):
        queryset = PolicyHolder.objects.filter(is_deleted=False).order_by('date_created')
        return DateUpdatedRequestParameterFilter(self.request).filter_queryset(queryset)

    @classmethod
    def _get_type_from_body(cls, request):
        try:
            # See: http://hl7.org/fhir/R4/organization.html
            return request.data['type'][0]['coding'][0]['code'].lower()
        except KeyError:
            return None

    @classmethod
    def _get_type_from_query(cls, request):
        try:
            return request.GET['resourceType'].lower()
        except KeyError:
            return None
