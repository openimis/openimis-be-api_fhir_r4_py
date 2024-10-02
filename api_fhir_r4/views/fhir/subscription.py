from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.exceptions import PermissionDenied, APIException
from rest_framework.viewsets import ModelViewSet

from api_fhir_r4.models import Subscription
from api_fhir_r4.openapi_schema_extensions import get_inline_error_serializer
from api_fhir_r4.permissions import FHIRApiSubscriptionPermissions
from api_fhir_r4.subscriptions import SubscriptionSerializer
from api_fhir_r4.services import SubscriptionService
from api_fhir_r4.subscriptions.subscriptionSerializer import SubscriptionSerializerSchema
from api_fhir_r4.views.fhir.base import BaseFHIRView
from api_fhir_r4.views.filters import DateUpdatedRequestParameterFilter
from api_fhir_r4.mixins import ListModelMixin, RetrieveModelMixin

@extend_schema_view(
    list=extend_schema(responses={(200, 'application/json'): SubscriptionSerializerSchema()}),
    retrieve=extend_schema(responses={
        (200, 'application/json'): SubscriptionSerializerSchema(),
        (404, 'application/json'): get_inline_error_serializer()
    }),
    create=extend_schema(
        request=SubscriptionSerializerSchema(),
        responses={(201, 'application/json'): SubscriptionSerializerSchema()}
    ),
    update=extend_schema(
        request=SubscriptionSerializerSchema(),
        responses={(200, 'application/json'): SubscriptionSerializerSchema()}
    ),
    destroy=extend_schema(responses={204: None})
)
class SubscriptionViewSet(BaseFHIRView, ListModelMixin, RetrieveModelMixin, ModelViewSet):
    _error_while_deleting = 'Error while deleting a subscription: %(msg)s'
    serializer_class = SubscriptionSerializer
    http_method_names = ('get', 'post', 'put', 'delete')
    permission_classes = (FHIRApiSubscriptionPermissions,)

    def get_queryset(self):
        queryset = Subscription.objects.filter(is_deleted=False).order_by('date_created')
        return DateUpdatedRequestParameterFilter(self.request).filter_queryset(queryset)

    def perform_destroy(self, instance):
        if not self.check_if_owner(self.request.user, instance):
            raise PermissionDenied(
                detail=self._error_while_deleting % {'msg': 'You are not the owner of this subscription'})
        service = SubscriptionService(self.request.user)
        result = service.delete({'id': instance.uuid})
        self.check_error_message(result)

    @staticmethod
    def check_error_message(result):
        if not result.get('success', False):
            msg = result.get('message', 'Unknown')
            raise APIException(f'Error while deleting a subscription: {msg}')

    @staticmethod
    def check_if_owner(user, instance):
        return str(user.id).lower() == str(instance.user_created.id).lower()
