from api_fhir_r4.converters import InsuranceOrganisationConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


class InsuranceOrganizationSerializer(BaseFHIRSerializer):
    fhirConverter = InsuranceOrganisationConverter

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
