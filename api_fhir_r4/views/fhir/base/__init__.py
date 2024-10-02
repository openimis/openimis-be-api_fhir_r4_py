from rest_framework.views import APIView

from api_fhir_r4.multiserializer import MultiSerializerSerializerClass
from api_fhir_r4.paginations import FhirBundleResultsSetPagination
from api_fhir_r4.permissions import FHIRApiPermissions
from api_fhir_r4.views import CsrfExemptSessionAuthentication
from api_fhir_r4.mixins import (
    UpdateModelMixin,
    ListModelMixin,
    CreateModelMixin,
    DestroyModelMixin
)


class BaseFHIRView(
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    APIView,

):
    user = None
    pagination_class = FhirBundleResultsSetPagination
    permission_classes = (FHIRApiPermissions,)
    authentication_classes = [CsrfExemptSessionAuthentication] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES


class BaseMultiserializerFHIRView(BaseFHIRView):
    serializer_class = MultiSerializerSerializerClass
