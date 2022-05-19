from api_fhir_r4.serializers import CodeSystemSerializer

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api_fhir_r4.permissions import FHIRApiInsureePermissions

from rest_framework.views import APIView
from api_fhir_r4.views import CsrfExemptSessionAuthentication
from django.core.exceptions import PermissionDenied


class CodeSystemOpenIMISPatientEducationLevelViewSet(viewsets.ViewSet):

    serializer_class = CodeSystemSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [CsrfExemptSessionAuthentication] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES

    def list(self, request):
        # we don't use typical instance, we only indicate the model and the field to be mapped into CodeSystem
        if not request.user.has_perms(FHIRApiInsureePermissions.permissions_get):
            raise PermissionDenied("unauthorized")
        serializer = CodeSystemSerializer(
            instance=None,
            **{
                "model_name": 'Education',
                "code_field": 'id',
                "display_field": 'education',
                "id": 'patient-education-level',
                "name": 'PatientEducationLevelCS',
                "title": 'Education Level (Patient)',
                "description": "Indicates the Education level of a Patient. "
                               "Values defined by openIMIS. Can be extended.",
                "url": self.request.build_absolute_uri()
            }
        )
        data = serializer.to_representation(obj=None)
        return Response(data)
