from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.converters import ClaimAdminPractitionerRoleConverter
from fhir.resources.identifier import Identifier
from fhir.resources.practitionerrole import PractitionerRole
from fhir.resources.reference import Reference
from api_fhir_r4.tests import GenericTestMixin, ClaimAdminPractitionerTestMixin, LocationTestMixin
from location.models import HealthFacility


class ClaimAdminPractitionerRoleTestMixin(GenericTestMixin):

    _TEST_CLAIM_ADMIN = None
    _TEST_HF = None
    _TEST_ORGANIZATION_REFERENCE = None
    _TEST_PRACTITIONER_REFERENCE = None

    _TEST_ID = 1
    _TEST_UUID = "254f6268-964b-4d8d-aa26-20081f22235e"
    _TEST_CODE = "1234abcd"

    _TEST_HF_ID = 10000
    _TEST_HF_UUID = "6d0eea8c-62eb-11ea-94d6-c36229a16c2f"
    _TEST_HF_CODE = "12345678"
    _TEST_HF_NAME = "TEST_NAME"
    _TEST_HF_LEVEL = "H"
    _TEST_HF_LEGAL_FORM = "G"
    _TEST_ADDRESS = "TEST_ADDRESS"
    _TEST_PHONE = "133-996-476"
    _TEST_FAX = "1-408-999 8888"
    _TEST_EMAIL = "TEST@TEST.com"

    def setUp(self):
        self._TEST_CLAIM_ADMIN = ClaimAdminPractitionerTestMixin().create_test_imis_instance()
        self._TEST_CLAIM_ADMIN.save()
        self._TEST_PRACTITIONER_REFERENCE = "Practitioner/" + self._TEST_CLAIM_ADMIN.uuid
        self._TEST_HF = self.create_test_health_facility()
        self._TEST_ORGANIZATION_REFERENCE = "Organization/" + self._TEST_HF.uuid

    def create_test_health_facility(self):
        location = LocationTestMixin().create_test_imis_instance()
        location.save()
        hf = HealthFacility()
        hf.id = self._TEST_HF_ID
        hf.uuid = self._TEST_HF_UUID
        hf.code = self._TEST_HF_CODE
        hf.name = self._TEST_HF_NAME
        hf.level = self._TEST_HF_LEVEL
        hf.legal_form_id = self._TEST_HF_LEGAL_FORM
        hf.address = self._TEST_ADDRESS
        hf.phone = self._TEST_PHONE
        hf.fax = self._TEST_FAX
        hf.email = self._TEST_EMAIL
        hf.location_id = location.id
        hf.offline = False
        hf.audit_user_id = -1
        hf.save()
        return hf

    def create_test_imis_instance(self):
        self._TEST_CLAIM_ADMIN.health_facility = self._TEST_HF
        return self._TEST_CLAIM_ADMIN

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_HF.code, imis_obj.health_facility.code)

    def create_test_fhir_instance(self):
        fhir_practitioner_role = PractitionerRole.construct()
        identifiers = []
        code = ClaimAdminPractitionerRoleConverter.build_fhir_identifier(
            self._TEST_CODE,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        identifiers.append(code)
        fhir_practitioner_role.identifier = identifiers
        organization_reference = Reference.construct()
        organization_reference.reference = self._TEST_ORGANIZATION_REFERENCE
        fhir_practitioner_role.organization = organization_reference
        practitioner_reference = Reference.construct()
        practitioner_reference.reference = self._TEST_PRACTITIONER_REFERENCE
        fhir_practitioner_role.practitioner = practitioner_reference
        return fhir_practitioner_role

    def verify_fhir_instance(self, fhir_obj):
        self.assertIn(self._TEST_ORGANIZATION_REFERENCE, fhir_obj.organization.reference)
        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = ClaimAdminPractitionerRoleConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_generic_type_code():
                self.assertEqual(self._TEST_CODE, identifier.value)
            elif code == R4IdentifierConfig.get_fhir_uuid_type_code():
                self.assertEqual(self._TEST_UUID, identifier.value)
        self.assertIn(self._TEST_PRACTITIONER_REFERENCE, fhir_obj.practitioner.reference)
        self.assertEqual(1, len(fhir_obj.code))
        self.assertEqual(1, len(fhir_obj.code[0].coding))
        self.assertEqual("CA", fhir_obj.code[0].coding[0].code)
        self.assertEqual("Claim Administrator",  fhir_obj.code[0].coding[0].display)
