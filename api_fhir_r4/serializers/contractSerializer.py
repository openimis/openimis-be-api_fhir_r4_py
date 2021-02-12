from api_fhir_r4.converters.contractConverter import ContractConverter
from api_fhir_r4.serializers import BaseFHIRSerializer
# from api_fhir_r4.models import Coverage, CoverageClass, Contract
# from rest_framework import serializers

class ContractSerializer(BaseFHIRSerializer):
    fhirConverter = ContractConverter

    