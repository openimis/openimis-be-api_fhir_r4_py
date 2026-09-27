from rest_framework.views import APIView

from api_fhir_r4.multiserializer import MultiSerializerSerializerClass
from api_fhir_r4.paginations import FhirBundleResultsSetPagination
from rest_framework.permissions import IsAuthenticated

from api_fhir_r4.permissions import FHIRApiPermissions
from api_fhir_r4.views import CsrfExemptSessionAuthentication
from api_fhir_r4.mixins import (
    UpdateModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
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
    authentication_classes = [
        CsrfExemptSessionAuthentication
    ] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES


class BaseMultiserializerFHIRView(
    UpdateModelMixin,
    DestroyModelMixin,
    APIView,
):
    user = None
    pagination_class = FhirBundleResultsSetPagination
    # Authentication only: on a multiserializer view, the real right is carried by the
    # permissions tuple of each registered serializer, and
    # `_get_eligible_from_user_permissions` refuses when none passes. That is what
    # GenericMultiSerializerViewsetMixin.permission_classes' docstring already says -
    # but that property is **shadowed** by the class attribute declared here, higher up
    # in the MRO. So these views in fact relied on FHIRApiPermissions, whose empty
    # lists let everything through: a check in appearance, not a check.
    permission_classes = (IsAuthenticated,)
    authentication_classes = [
        CsrfExemptSessionAuthentication
    ] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES
    serializer_class = MultiSerializerSerializerClass
