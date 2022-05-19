from api_fhir_r4.converters import BillInvoiceConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


class BillSerializer(BaseFHIRSerializer):
    fhirConverter = BillInvoiceConverter()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
