from rest_framework.serializers import Serializer


class MultiSerializerSerializerClass(Serializer):
    """
     Serves as base serializer class for instances using multiserializer mixin.
     """

    def update(self, instance, validated_data):
        raise NotImplementedError("MultiSerializerSerializerClass `update` not supported. Should be"
                                  "performed by contained serializers")

    def create(self, validated_data):
        raise NotImplementedError("MultiSerializerSerializerClass `create` not supported. Should be"
                                  "performed by contained serializers")

    def to_representation(self, instance):
        """
        This override is required by rest framework serializer logic. During render the serilaizer to_representation()
        is called. However multiserializer aggregate output data using mixins. Therefore by default IMIS FHIR approach
        calls BaseFhirSerializer to_representation() which cause not implemented exception.
        :param instance:
        :return:
        """
        return {}
