from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from api_fhir_r4.converters import OperationOutcomeConverter
from api_fhir_r4.mixins import MultiIdentifierRetrieverMixin, MultiIdentifierUpdateMixin
from api_fhir_r4.model_retrievers import UUIDIdentifierModelRetriever, CHFIdentifierModelRetriever
from api_fhir_r4.permissions import FHIRApiInsureePermissions
from api_fhir_r4.serializers import PatientSerializer, CodeSystemSerializer
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import ValidityFromRequestParameterFilter
from api_fhir_r4.views import CsrfExemptSessionAuthentication
from claim.models import Claim
from insuree.models import Insuree
from django.core.exceptions import PermissionDenied


class InsureeViewSet(BaseFHIRView, MultiIdentifierRetrieverMixin,
                     MultiIdentifierUpdateMixin, viewsets.ModelViewSet):
    retrievers = [UUIDIdentifierModelRetriever, CHFIdentifierModelRetriever]
    serializer_class = PatientSerializer
    permission_classes = (FHIRApiInsureePermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("identifier")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from')
        serializer = PatientSerializer(self.paginate_queryset(queryset), many=True, user=request.user)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        insurer_qs = Insuree.get_queryset(None, self.request.user)
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(insurer_qs)


class CodeSystemOpenIMISPatientEducationLevelViewSet(viewsets.ViewSet):
    serializer_class = CodeSystemSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [CsrfExemptSessionAuthentication] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES

    def list(self, request):
        if not request.user.has_perms(FHIRApiInsureePermissions.permissions_get):
            raise PermissionDenied("unauthorized")
        serializer = CodeSystemSerializer(
            user=request.user,
            instance=None,
            **{
                "model_name": 'Education',
                "code_field": 'id',
                "display_field": 'education',
                "id": 'patient-education-level',
                "name": 'PatientEducationLevelCS',
                "title": 'Education Level (Patient)',
                "description": "Indicates the Education level of a Patient. Values defined by openIMIS. Can be extended.",
                "url": self.request.build_absolute_uri()
            }
        )
        data = serializer.to_representation(obj=None)
        return Response(data)


class CodeSystemOpenIMISPatientProfessionViewSet(viewsets.ViewSet):
    serializer_class = CodeSystemSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [CsrfExemptSessionAuthentication] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES

    def list(self, request):
        if not request.user.has_perms(FHIRApiInsureePermissions.permissions_get):
            raise PermissionDenied("unauthorized")
        serializer = CodeSystemSerializer(
            user=request.user,
            instance=None,
            **{
                "model_name": 'Profession',
                "code_field": 'id',
                "display_field": 'profession',
                "id": 'patient-profession',
                "name": 'PatientProfessionCS',
                "title": 'Profession (Patient)',
                "description": "Indicates the Profession of a Patient. Values defined by openIMIS.",
                "url": self.request.build_absolute_uri()
            }
        )
        data = serializer.to_representation(obj=None)
        return Response(data)


class CodeSystemOpenIMISPatientIdentificationTypeViewSet(viewsets.ViewSet):
    serializer_class = CodeSystemSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [CsrfExemptSessionAuthentication] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES

    def list(self, request):
        if not request.user.has_perms(FHIRApiInsureePermissions.permissions_get):
            raise PermissionDenied("unauthorized")
        serializer = CodeSystemSerializer(
            user=request.user,
            instance=None,
            **{
                "model_name": 'IdentificationType',
                "code_field": 'id',
                "display_field": 'identification_type',
                "id": 'patient-identification-type',
                "name": 'PatientIdentificationTypeCS',
                "title": 'Identification Type (Patient)',
                "description": "Indicates the Identification Type of a Patient. Values defined by openIMIS.",
                "url": self.request.build_absolute_uri()
            }
        )
        data = serializer.to_representation(obj=None)
        return Response(data)


class CodeSystemOpenIMISPatientRelationshipViewSet(viewsets.ViewSet):
    serializer_class = CodeSystemSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [CsrfExemptSessionAuthentication] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES

    def list(self, request):
        if not request.user.has_perms(FHIRApiInsureePermissions.permissions_get):
            raise PermissionDenied("unauthorized")
        serializer = CodeSystemSerializer(
            user=request.user,
            instance=None,
            **{
                "model_name": 'Relation',
                "code_field": 'id',
                "display_field": 'relation',
                "id": 'patient-contact-relationship',
                "name": 'PatientContactRelationshipCS',
                "title": 'Contact Relationship (Patient)',
                "description": "Indicates the Relationship of a Patient with the Head of the Family. Values defined by openIMIS.",
                "url": self.request.build_absolute_uri()
            }
        )
        data = serializer.to_representation(obj=None)
        return Response(data)



