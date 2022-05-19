from api_fhir_r4.converters import ClaimAdminPractitionerRoleConverter
from fhir.resources.practitionerrole import PractitionerRole
from api_fhir_r4.tests import ClaimAdminPractitionerRoleTestMixin
from api_fhir_r4.tests.mixin import ConvertJsonToFhirTestMixin, ConvertToFhirTestMixin, ConvertToImisTestMixin


class ClaimAdminPractitionerRoleConverterTestCase(ClaimAdminPractitionerRoleTestMixin,
                                                  ConvertToImisTestMixin,
                                                  ConvertToFhirTestMixin,
                                                  ConvertJsonToFhirTestMixin):
    converter = ClaimAdminPractitionerRoleConverter
    fhir_resource = PractitionerRole
    json_repr = 'test/test_claimAdminPractitionerRole.json'
