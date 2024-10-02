from api_fhir_r4.serializers import CodeSystemSerializer

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api_fhir_r4.permissions import FHIRApiGroupPermissions

from rest_framework.views import APIView
from api_fhir_r4.views import CsrfExemptSessionAuthentication
from django.core.exceptions import PermissionDenied


class CodeSystemOpenIMISGroupConfirmationTypeViewSet(viewsets.ViewSet):

    serializer_class = CodeSystemSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [CsrfExemptSessionAuthentication] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES

    def list(self, request):
        # we don't use typical instance, we only indicate the model and the field to be mapped into CodeSystem
        if not request.user.has_perms(FHIRApiGroupPermissions.permissions_get):
            raise PermissionDenied("unauthorized")
        serializer = CodeSystemSerializer(
            user=request.user,
            instance=None,
            **{
                "model_name": 'ConfirmationType',
                "code_field": 'code',
                "display_field": 'confirmationtype',
                "id": 'group-confirmation-type',
                "name": 'GroupConfirmationTypeCS',
                "title": 'Confirmation Types (Group)',
                "description": "Indicates the confirmation type for the Group. "
                               "Values defined by openIMIS. Can be extended.",
                "url": self.request.build_absolute_uri()
            }
        )
        data = serializer.to_representation(obj=None)
        return Response(data)
