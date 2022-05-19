from api_fhir_r4.converters import EnrolmentOfficerPractitionerConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


class EnrolmentOfficerPractitionerSerializer(BaseFHIRSerializer):

    fhirConverter = EnrolmentOfficerPractitionerConverter()
