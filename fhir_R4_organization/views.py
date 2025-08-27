import logging
from collections import defaultdict, OrderedDict
from datetime import datetime as py_datetime
from django.db.models import Q
from django.http import Http404
from itertools import chain
from rest_framework.request import Request
from rest_framework.response import Response

from api_fhir_r4.defaultConfig import DEFAULT_CFG
from api_fhir_r4.mixins import MultiIdentifierRetrieveManySerializersMixin, MultiIdentifierRetrieverMixin
from api_fhir_r4.model_retrievers import (
    CodeIdentifierModelRetriever,
    DatabaseIdentifierModelRetriever,
    UUIDIdentifierModelRetriever
)
from api_fhir_r4.multiserializer import modelViewset
from api_fhir_r4.permissions import (
    FHIRApiOrganizationPermissions,
    FHIRApiHealthServicePermissions,
    FHIRApiInsuranceOrganizationPermissions
)
from api_fhir_r4.views.fhir.base import BaseMultiserializerFHIRView
from api_fhir_r4.serializers import (
    PolicyHolderOrganisationSerializer,
    HealthFacilityOrganisationSerializer,
    InsuranceOrganizationSerializer
)
from api_fhir_r4.views.filters import (
    ValidityFromRequestParameterFilter,
    HealthFacilityLevelFilter
)
from location.models import HealthFacility
from policyholder.models import PolicyHolder


logger = logging.getLogger(__name__)


class OrganizationViewSet(BaseMultiserializerFHIRView, MultiIdentifierRetrieveManySerializersMixin,
                          MultiIdentifierRetrieverMixin, modelViewset.ModelViewSet):
    """
    FHIR Organization Resource ViewSet
    Maps openIMIS PolicyHolder and HealthFacility to FHIR Organization resource
    """
    retrievers = [UUIDIdentifierModelRetriever, DatabaseIdentifierModelRetriever, CodeIdentifierModelRetriever]
    lookup_field = 'identifier'

    @property
    def serializers(self):
        return [
            {
                'serializer': PolicyHolderOrganisationSerializer,
                'queryset': self._ph_queryset(),
                'permission_classes': [FHIRApiOrganizationPermissions]
            },
            {
                'serializer': HealthFacilityOrganisationSerializer,
                'queryset': self._hf_queryset(),
                'permission_classes': [FHIRApiHealthServicePermissions]
            },
            {
                'serializer': InsuranceOrganizationSerializer,
                'queryset': self._io_queryset(),
                'permission_classes': [FHIRApiInsuranceOrganizationPermissions]
            }
        ]

    def list(self, request, *args, **kwargs):
        identifier = request.GET.get("identifier")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            return super().list(request, *args, **kwargs)

    def _hf_queryset(self):
        queryset = HealthFacility.get_queryset(None, self.request.user)
        return HealthFacilityLevelFilter(self.request).filter_queryset(
            ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)
        )

    def _ph_queryset(self):
        queryset = PolicyHolder.get_queryset(None, self.request.user)
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)

    def _io_queryset(self):
        return self._get_insurance_organisations_as_list()

    def _get_insurance_organisations_as_list(self):
        return list(self._get_insurance_organisations().values())

    def _get_insurance_organisations(self):
        return DEFAULT_CFG.get('insurance_organisation_config', {})
