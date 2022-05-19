from api_fhir_r4.converters import EnrolmentOfficerPractitionerRoleConverter
from fhir.resources.practitionerrole import PractitionerRole
from api_fhir_r4.tests import EnrolmentOfficerPractitionerRoleTestMixin
from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class EnrolmentOfficerPractitionerRoleConverterTestCase(EnrolmentOfficerPractitionerRoleTestMixin,
                                                        ConvertToImisTestMixin,
                                                        ConvertToFhirTestMixin,
                                                        ConvertJsonToFhirTestMixin):
    converter = EnrolmentOfficerPractitionerRoleConverter
    fhir_resource = PractitionerRole
    json_repr = 'test/test_enrolmentOfficerPractitionerRole.json'
