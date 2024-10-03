from rest_framework.viewsets import GenericViewSet

from api_fhir_r4.permissions import FHIRApiCoverageEligibilityRequestPermissions
from api_fhir_r4.serializers import CoverageEligibilityRequestSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from insuree.models import Insuree


class CoverageEligibilityRequestViewSet(BaseFHIRView, GenericViewSet):
    queryset = Insuree.filter_queryset()
    serializer_class = CoverageEligibilityRequestSerializer
    permission_classes = (FHIRApiCoverageEligibilityRequestPermissions,)

    def get_queryset(self):
        queryset = Insuree.get_queryset(None, self.request.user)
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
