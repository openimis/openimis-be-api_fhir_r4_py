from api_fhir_r4.converters import PolicyHolderOrganisationConverter
from api_fhir_r4.tests.mixin.policyHolderOrganisationTestMixin import PolicyHolderOrganisationTestMixin


class PolicyHolderOrganisationConverterTestCase(PolicyHolderOrganisationTestMixin):
    def setUp(self):
        super(PolicyHolderOrganisationConverterTestCase, self).setUp()

    def test_to_fhir_obj(self):
        self.setUp()
        imis_product = self.create_test_imis_instance()
        fhir_insurance_plan = PolicyHolderOrganisationConverter.to_fhir_obj(imis_product)
        self.verify_fhir_instance(fhir_insurance_plan)
