from api_fhir_r4.multiserializer.modelViewset import MultiSerializerModelViewSet
from api_fhir_r4.serializers.itemsPricelistValueSetSerializer import ItemsPricelistValueSetSerializer
from api_fhir_r4.serializers.servicesPricelistValueSetSerializer import ServicesPricelistValueSetSerializer
from api_fhir_r4.permissions import FHIRApiMedicationPermissions, FHIRApiActivityDefinitionPermissions
from medical_pricelist.models import ItemsPricelistDetail, ServicesPricelistDetail

from rest_framework.views import APIView
from api_fhir_r4.views import CsrfExemptSessionAuthentication


class PricelistValueSetViewSet(MultiSerializerModelViewSet):
    authentication_classes = [
        CsrfExemptSessionAuthentication
    ] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES

    @property
    def serializers(self):
        return {
            ItemsPricelistValueSetSerializer: (
                lambda: ItemsPricelistDetail.objects.all(),
                self._items_validator,
                (FHIRApiMedicationPermissions,),
            ),
            ServicesPricelistValueSetSerializer: (
                lambda: ServicesPricelistDetail.objects.all(),
                self._services_validator,
                (FHIRApiActivityDefinitionPermissions,),
            ),
        }

    def _items_validator(self, context):
        """Validator for items pricelist - checks if URL contains 'items-pricelist'"""
        request = context.get('request')
        if request:
            return 'items-pricelist' in request.path
        return False

    def _services_validator(self, context):
        """Validator for services pricelist - checks if URL contains 'services-pricelist'"""
        request = context.get('request')
        if request:
            return 'services-pricelist' in request.path
        return False
