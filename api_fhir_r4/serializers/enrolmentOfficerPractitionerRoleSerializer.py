from api_fhir_r4.converters import EnrolmentOfficerPractitionerRoleConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


class EnrolmentOfficerPractitionerRoleSerializer(BaseFHIRSerializer):

    fhirConverter = EnrolmentOfficerPractitionerRoleConverter()
