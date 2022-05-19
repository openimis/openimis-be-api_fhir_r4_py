from api_fhir_r4.converters import PolicyHolderOrganisationConverter
from api_fhir_r4.tests.mixin import ConvertToFhirTestMixin
from api_fhir_r4.tests.mixin.policyHolderOrganisationTestMixin import PolicyHolderOrganisationTestMixin


class PolicyHolderOrganisationConverterTestCase(PolicyHolderOrganisationTestMixin,
                                                ConvertToFhirTestMixin):
    converter = PolicyHolderOrganisationConverter
