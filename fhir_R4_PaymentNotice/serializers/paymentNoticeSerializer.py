from api_fhir_r4.serializers import BaseFHIRSerializer
from fhir_R4_PaymentNotice.converters.paymentNoticeConverter import PaymentNoticeConverter


class PaymentNoticeSerializer(BaseFHIRSerializer):
    fhirConverter = PaymentNoticeConverter

    def create(self, validated_data):
        # PaymentNotice creation logic can be implemented here if needed
        pass

    def update(self, instance, validated_data):
        # PaymentNotice update logic can be implemented here if needed
        pass
