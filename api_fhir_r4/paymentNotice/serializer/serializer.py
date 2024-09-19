from .create import PaymentNoticeSerializerCreate
from api_fhir_r4.paymentNotice import PaymentNoticeConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


class PaymentNoticeSerializer(BaseFHIRSerializer):
    fhirConverter = PaymentNoticeConverter

    def create(self, validated_data):
        request = self.context.get("request")
        return PaymentNoticeSerializerCreate.create(validated_data, request)

    def update(self, instance, validated_data):
        pass
