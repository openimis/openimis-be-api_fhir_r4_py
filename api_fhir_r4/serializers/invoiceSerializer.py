from api_fhir_r4.converters import InvoiceConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


class InvoiceSerializer(BaseFHIRSerializer):
    fhirConverter = InvoiceConverter()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
