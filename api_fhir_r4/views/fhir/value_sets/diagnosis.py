import uuid
from urllib.parse import urljoin

from django.db.models import Q
from django.utils import timezone
from fhir.resources.R4B.valueset import ValueSet
from rest_framework import exceptions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api_fhir_r4.configurations import GeneralConfiguration, R4ClaimConfig
from api_fhir_r4.permissions import FHIRApiClaimPermissions
from api_fhir_r4.views import CsrfExemptSessionAuthentication
from medical.models import Diagnosis


class DiagnosisValueSetViewSet(viewsets.ViewSet):
    """Expose the diagnoses configured in openIMIS as a FHIR ValueSet."""

    lookup_value_regex = "diagnosis"
    permission_classes = (IsAuthenticated,)
    authentication_classes = [
        CsrfExemptSessionAuthentication
    ] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES

    def retrieve(self, request, pk=None):
        self._check_permissions(request)
        return Response(self._build_value_set().dict())

    @action(detail=True, methods=["get"], url_path=r"\$expand")
    def expand(self, request, pk=None):
        self._check_permissions(request)

        filter_value = request.query_params.get("filter", "").strip()
        offset = self._get_non_negative_integer(request, "offset", 0)
        count = self._get_non_negative_integer(
            request,
            "count",
            GeneralConfiguration.get_default_response_page_size(),
        )

        queryset = Diagnosis.get_queryset(None, request.user).order_by("code", "id")
        if filter_value:
            queryset = queryset.filter(
                Q(code__icontains=filter_value) | Q(name__icontains=filter_value)
            )

        total = queryset.count()
        diagnoses = queryset[offset:offset + count]
        expansion = self._build_expansion(
            diagnoses, total, offset, count, filter_value
        )
        return Response(self._build_value_set(expansion=expansion).dict())

    def _build_value_set(self, expansion=None):
        system = self._canonical_url(
            R4ClaimConfig.get_fhir_claim_diagnosis_system()
        )
        system_version = R4ClaimConfig.get_fhir_claim_diagnosis_system_version()
        include = {"system": system}
        if system_version:
            include["version"] = system_version

        value_set = {
            "id": "diagnosis",
            "url": self._canonical_url(
                R4ClaimConfig.get_fhir_claim_diagnosis_value_set()
            ),
            "name": "OpenIMISDiagnosisValueSet",
            "title": "openIMIS Diagnosis Value Set",
            "status": "active",
            "description": "The diagnoses currently configured in openIMIS.",
            "compose": {"include": [include]},
        }
        if expansion is not None:
            value_set["expansion"] = expansion
        return ValueSet(**value_set)

    def _build_expansion(self, diagnoses, total, offset, count, filter_value):
        system = self._canonical_url(
            R4ClaimConfig.get_fhir_claim_diagnosis_system()
        )
        system_version = R4ClaimConfig.get_fhir_claim_diagnosis_system_version()
        contains = []
        for diagnosis in diagnoses:
            concept = {
                "system": system,
                "code": diagnosis.code,
                "display": diagnosis.name,
            }
            if system_version:
                concept["version"] = system_version
            contains.append(concept)

        parameters = [
            {"name": "offset", "valueInteger": offset},
            {"name": "count", "valueInteger": count},
        ]
        if filter_value:
            parameters.append({"name": "filter", "valueString": filter_value})

        return {
            "identifier": f"urn:uuid:{uuid.uuid4()}",
            "timestamp": timezone.now().isoformat(),
            "total": total,
            "offset": offset,
            "parameter": parameters,
            "contains": contains,
        }

    @staticmethod
    def _canonical_url(value):
        return urljoin(GeneralConfiguration.get_system_base_url(), value)

    @staticmethod
    def _get_non_negative_integer(request, name, default):
        value = request.query_params.get(name)
        if value is None:
            return default
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise exceptions.ParseError(
                f"The {name} parameter must be a non-negative integer."
            )
        if value < 0:
            raise exceptions.ParseError(
                f"The {name} parameter must be a non-negative integer."
            )
        return value

    @staticmethod
    def _check_permissions(request):
        if not request.user.has_perms(FHIRApiClaimPermissions.permissions_get):
            raise exceptions.PermissionDenied("unauthorized")
