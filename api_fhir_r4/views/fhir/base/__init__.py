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
    # Authentification seulement : sur une vue multiserializer, le droit reel est porte
    # par le tuple de permissions de chaque serializer enregistre, et
    # `_get_eligible_from_user_permissions` refuse si aucun ne passe. C'est ce que dit
    # deja la docstring de GenericMultiSerializerViewsetMixin.permission_classes - mais
    # cette propriete est **masquee** par l'attribut de classe declare ici, plus haut
    # dans le MRO. Ces vues s'appuyaient donc en fait sur FHIRApiPermissions, dont les
    # listes vides laissent tout passer : un controle d'apparence, pas un controle.
    permission_classes = (IsAuthenticated,)
    authentication_classes = [
        CsrfExemptSessionAuthentication
    ] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES
    serializer_class = MultiSerializerSerializerClass
