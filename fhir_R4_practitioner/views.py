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
from core.models.user import ClaimAdmin
from core.models import Officer


logger = logging.getLogger(__name__)


class PractitionerViewSet(BaseMultiserializerFHIRView, MultiIdentifierRetrieveManySerializersMixin,
                          MultiIdentifierRetrieverMixin, modelViewset.ModelViewSet):
    """
    FHIR Practitioner Resource ViewSet
    Maps openIMIS ClaimAdmin and Officer to FHIR Practitioner resource
    """
    retrievers = [UUIDIdentifierModelRetriever, CodeIdentifierModelRetriever]
    serializers = [
        {
            'serializer': ClaimAdminPractitionerSerializer,
            'queryset': ClaimAdmin.objects.all(),
            'permission_classes': [FHIRApiPractitionerClaimAdminPermissions]
        },
        {
            'serializer': EnrolmentOfficerPractitionerSerializer,
            'queryset': Officer.objects.all(),
            'permission_classes': [FHIRApiPractitionerOfficerPermissions]
        }
    ]

    def list(self, request: Request, *args, **kwargs):
        identifier = request.GET.get("identifier")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            return super().list(request, *args, **kwargs)

    def get_base_queryset(self, queryset, serializer_class):
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
