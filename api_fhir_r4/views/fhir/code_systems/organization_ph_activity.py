from api_fhir_r4.serializers import CodeSystemSerializer

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from rest_framework.views import APIView
from api_fhir_r4.views import CsrfExemptSessionAuthentication
from policyholder.services import PolicyHolderActivity


class CodeSystemOrganizationPHActivityViewSet(viewsets.ViewSet):
    serializer_class = CodeSystemSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [CsrfExemptSessionAuthentication] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES

    def list(self, request):
        # we don't use typical instance, we only indicate the model and the field to be mapped into CodeSystem
        serializer = CodeSystemSerializer(
            instance=None,
            **{
                'data': PolicyHolderActivity(request.user).get_all()['data'],
                'code_field': 'code',
                'display_field': 'display',
                'id': 'organization-ph-activity',
                "name": 'OrganizationPHActivityCS',
                "title": 'Activity (Organization)',
                "description": "Indicates the activity of the PolicyHolder Organization. "
                               "Values defined by openIMIS. Can be extended.",
                "url": self.request.build_absolute_uri()
            }
        )
        data = serializer.to_representation(obj=None)
        return Response(data)
