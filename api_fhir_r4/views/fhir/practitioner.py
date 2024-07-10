import logging

from rest_framework.request import Request

from api_fhir_r4.mixins import (
    MultiIdentifierRetrieveManySerializersMixin,
    MultiIdentifierRetrieverMixin
)
from api_fhir_r4.model_retrievers import (
    UUIDIdentifierModelRetriever,
    CodeIdentifierModelRetriever
)
from api_fhir_r4.multiserializer import modelViewset
from api_fhir_r4.permissions import (
    FHIRApiPractitionerClaimAdminPermissions,
    FHIRApiPractitionerOfficerPermissions
)
from api_fhir_r4.serializers import (
    ClaimAdminPractitionerSerializer,
    EnrolmentOfficerPractitionerSerializer
)
from api_fhir_r4.views.fhir.base import BaseMultiserializerFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from claim.models import ClaimAdmin
from core.models import Officer


logger = logging.getLogger(__name__)


class PractitionerViewSet(BaseMultiserializerFHIRView,
                          modelViewset.MultiSerializerModelViewSet,
                          MultiIdentifierRetrieveManySerializersMixin, MultiIdentifierRetrieverMixin):
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]

    lookup_field = 'identifier'

    @property
    def serializers(self):
        return {
            ClaimAdminPractitionerSerializer:
                (self._ca_queryset(), self._ca_serializer_validator, (FHIRApiPractitionerClaimAdminPermissions,)),
            EnrolmentOfficerPractitionerSerializer:
                (self._eo_queryset(), self._eo_serializer_validator, (FHIRApiPractitionerOfficerPermissions,)),
        }

    @classmethod
    def _ca_serializer_validator(cls, context):
        return cls._base_request_validator_dispatcher(
            request=context['request'],
            get_check=lambda x: cls._get_type_from_query(x) in ('ca', None),
            post_check=lambda x: cls._get_type_from_body(x) == 'ca',
            put_check=lambda x: cls._get_type_from_body(x) in ('ca', None),
        )

    @classmethod
    def _eo_serializer_validator(cls, context):
        return cls._base_request_validator_dispatcher(
            request=context['request'],
            get_check=lambda x: cls._get_type_from_query(x) in ('eo', None),
            post_check=lambda x: cls._get_type_from_body(x) == 'eo',
            put_check=lambda x: cls._get_type_from_body(x) in ('eo', None),
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
        return ClaimAdmin.objects

    def _ca_queryset(self):
        queryset = ClaimAdmin\
            .objects\
            .filter(validity_to__isnull=True).all()
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)

    def _eo_queryset(self):
        queryset = Officer.objects.filter(validity_to__isnull=True).order_by('validity_from').all()
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)

    @classmethod
    def _get_type_from_body(cls, request):
        try:
            # See: http://hl7.org/fhir/R4/practitioner.html
            return request.data['qualification'][0]['code']['coding'][0]['code'].lower()
        except KeyError:
            logger.exception(
                "Failed to match IMIS practitioner type using request body. It should be accessible under"
                "body.qualification[0].code.coding[0].code")
            return None

    @classmethod
    def _get_type_from_query(cls, request):
        try:
            return request.GET['resourceType'].lower()
        except KeyError:
            return None

    def _raise_no_eligible_serializer(self):
        raise AssertionError(
            "Failed to match serializer eligible for given request. "
            "For POST request JSON should determine eo/ca type in body.type[0].coding[0].code")

    def _raise_multiple_eligible_serializers(self):
        raise AssertionError(
            "Ambiguous request, more than one serializer is eligible for given action. ")
