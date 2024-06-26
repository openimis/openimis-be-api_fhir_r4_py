from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.converters import ClaimAdminPractitionerRoleConverter
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.practitionerrole import PractitionerRole
from fhir.resources.R4B.reference import Reference
from api_fhir_r4.tests import GenericTestMixin,  LocationTestMixin
from location.models import HealthFacility
from location.test_helpers import create_test_village, create_test_health_facility
from claim.test_helpers import create_test_claim_admin
from api_fhir_r4.utils import TimeUtils

class ClaimAdminPractitionerRoleTestMixin(GenericTestMixin):
    test_claim_admin = None
    test_hf = None
    test_village = None
    _TEST_ORGANIZATION_REFERENCE = None
    _TEST_CLAIM_ADMIN_PRACTITIONER_REFERENCE = None

    _TEST_CLAIM_ADMIN_ID = 1
    _TEST_CLAIM_ADMIN_UUID = "254f6268-964b-4d8d-aa26-20081f22235e"
    _TEST_CLAIM_ADMIN_CODE = "1234abcd"
    
    _TEST_CLAIM_ADMIN_DOB = "1990-03-24"

    _TEST_HF_ID = 10000
    _TEST_HF_UUID = "6d0eea8c-62eb-11ea-94d6-c36229a16c2f"
    _TEST_HF_CODE = "12345678"
    _TEST_HF_NAME = "TEST_NAME"
    _TEST_HF_LEVEL = "H"
    _TEST_HF_LEGAL_FORM = "G"
    _TEST_CLAIM_ADMIN_ADDRESS = "TEST_ADDRESS"
    _TEST_CLAIM_ADMIN_PHONE = "133-996-476"
    _TEST_CLAIM_ADMIN_FAX = "1-408-999 8888"
    _TEST_CLAIM_ADMIN_EMAIL = "TEST@TEST.com"
    sub_str = {}

    def setUp(self):
        super(ClaimAdminPractitionerRoleTestMixin, self).setUp()
        self.test_village= create_test_village()
        self.test_hf = self.create_test_hf()
        self.test_claim_admin = create_test_claim_admin( custom_props={
            'health_facility_id': self.test_hf.id, 
            'code':self._TEST_CLAIM_ADMIN_CODE,
            'dob':TimeUtils.str_to_date(self._TEST_CLAIM_ADMIN_DOB),
            'phone':self._TEST_CLAIM_ADMIN_PHONE})
        self._TEST_CLAIM_ADMIN_PRACTITIONER_REFERENCE = "Practitioner/" + str(self.test_claim_admin.uuid)
        self._TEST_ORGANIZATION_REFERENCE = "Organization/" + str(self.test_hf.uuid)
        self.sub_str[self._TEST_HF_UUID]=self.test_hf.uuid
        self.sub_str[self._TEST_CLAIM_ADMIN_UUID]=self.test_claim_admin.uuid
        self._TEST_HF_UUID=self.test_hf.uuid
        self._TEST_HF_ID=self.test_hf.id

    def create_test_hf(self):
        self.test_hf = create_test_health_facility(
            self._TEST_HF_CODE,
            self.test_village.parent.parent.id,
            custom_props = {
                'name': self._TEST_HF_NAME,
                'level':self._TEST_HF_LEVEL,
                'legal_form_id':self._TEST_HF_LEGAL_FORM,

            }
        )
        return self.test_hf


    def create_test_imis_instance(self):
        self.test_claim_admin.health_facility = self.test_hf
        return self.test_claim_admin

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self.test_hf.code, imis_obj.health_facility.code)

    def create_test_fhir_instance(self):
        fhir_practitioner_role = PractitionerRole.construct()
        identifiers = []
        code = ClaimAdminPractitionerRoleConverter.build_fhir_identifier(
            self._TEST_CLAIM_ADMIN_CODE,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        identifiers.append(code)
        fhir_practitioner_role.identifier = identifiers
        organization_reference = Reference.construct()
        organization_reference.reference = self._TEST_ORGANIZATION_REFERENCE
        fhir_practitioner_role.organization = organization_reference
        practitioner_reference = Reference.construct()
        practitioner_reference.reference = self._TEST_CLAIM_ADMIN_PRACTITIONER_REFERENCE
        fhir_practitioner_role.practitioner = practitioner_reference
        return fhir_practitioner_role

    def verify_fhir_instance(self, fhir_obj):
        self.assertIn(self._TEST_ORGANIZATION_REFERENCE, fhir_obj.organization.reference)
        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = ClaimAdminPractitionerRoleConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_generic_type_code():
                self.assertEqual(self.test_claim_admin.code, identifier.value)
            elif code == R4IdentifierConfig.get_fhir_uuid_type_code():
                self.assertEqual(str(self.test_claim_admin.uuid), identifier.value)
        self.assertIn(self._TEST_CLAIM_ADMIN_PRACTITIONER_REFERENCE, fhir_obj.practitioner.reference)
        self.assertEqual(1, len(fhir_obj.code))
        self.assertEqual(1, len(fhir_obj.code[0].coding))
        self.assertEqual("CA", fhir_obj.code[0].coding[0].code)
        self.assertEqual("Claim Administrator", fhir_obj.code[0].coding[0].display)
