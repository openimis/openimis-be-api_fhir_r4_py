from abc import ABC

from api_fhir_r4.multiserializer import mixins
from rest_framework.viewsets import GenericViewSet

from api_fhir_r4.multiserializer.serializerClass import MultiSerializerSerializerClass


class MultiSerializerModelViewSet(
        GenericViewSet,
        mixins.MultiSerializerCreateModelMixin,
        mixins.MultiSerializerRetrieveModelMixin,
        mixins.MultiSerializerUpdateModelMixin,
        mixins.MultiSerializerListModelMixin, ABC
):
    serializer_class = MultiSerializerSerializerClass
