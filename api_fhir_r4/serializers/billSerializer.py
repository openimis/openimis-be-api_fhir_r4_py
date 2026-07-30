from api_fhir_r4.converters.invoiceConverter import BillInvoiceConverter
from api_fhir_r4.serializers.baseSerializer import BaseFHIRSerializer


class BillSerializer(BaseFHIRSerializer):
    fhirConverter = BillInvoiceConverter

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
