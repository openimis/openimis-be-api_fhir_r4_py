from fhir.resources.practitionerrole import PractitionerRole
from fhir.resources.extension import Extension
from fhir.resources.identifier import Identifier
from fhir.resources.reference import Reference
from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import EnrolmentOfficerPractitionerConverter, EnrolmentOfficerPractitionerRoleConverter
from api_fhir_r4.tests import GenericTestMixin, EnrolmentOfficerPractitionerTestMixin, LocationTestMixin
from core.models import Officer


class EnrolmentOfficerPractitionerRoleTestMixin(GenericTestMixin):

    _TEST_OFFICER = None
    _TEST_LOCATION = None
    _TEST_SUBSTITUTION_OFFICER = None
    _TEST_SUBSTITUTION_OFFICER_UUID = "f4bf924a-e2c9-46dc-9fa3-d54a1a67ea86"
    _TEST_SUBSTITUTION_OFFICER_CODE = "EOTESB"
    _TEST_PRACTITIONER_REFERENCE = None
    _TEST_LOCATION_REFERENCE = None
    _TEST_LOCATION_UUID = "041890f3-d90b-46ca-8b25-56c3f8d60615"

    def setUp(self):
        self._TEST_OFFICER = EnrolmentOfficerPractitionerTestMixin().create_test_imis_instance()
        self._TEST_SUBSTITUTION_OFFICER = self.create_test_subsitution_officer()
        self._TEST_PRACTITIONER_REFERENCE = "Practitioner/" + self._TEST_OFFICER.uuid
        self._TEST_LOCATION = self.create_test_location()
        self._TEST_LOCATION_REFERENCE = "Location/" + self._TEST_LOCATION.uuid

    def create_test_subsitution_officer(self):
        officer = Officer.objects.create(
            **{
                "uuid": self._TEST_SUBSTITUTION_OFFICER_UUID,
                "code": self._TEST_SUBSTITUTION_OFFICER_CODE,
                "last_name": "Officer",
                "other_names": "Test",
                "validity_to": None,
                "audit_user_id": -1,
            }
        )
        return officer

    def create_test_location(self):
        location = LocationTestMixin().create_test_imis_instance()
        location.uuid = self._TEST_LOCATION_UUID
        location.save()
        return location

    def create_test_imis_instance(self):
        self._TEST_OFFICER.location = self._TEST_LOCATION
        self._TEST_OFFICER.substitution_officer = self._TEST_SUBSTITUTION_OFFICER
        self._TEST_OFFICER.audit_user_id = -1
        self._TEST_OFFICER.save()
        return self._TEST_OFFICER

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_OFFICER.substitution_officer.code, imis_obj.substitution_officer.code)
        self.assertEqual(self._TEST_LOCATION.code, imis_obj.location.code)

    def create_test_fhir_instance(self):
        self.create_test_imis_instance()
        fhir_practitioner_role = PractitionerRole.construct()
        identifiers = []
        code = EnrolmentOfficerPractitionerRoleConverter.build_fhir_identifier(
            self._TEST_OFFICER.code,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        identifiers.append(code)
        location_reference = Reference.construct()
        location_reference.reference = self._TEST_LOCATION_REFERENCE
        fhir_practitioner_role.location = [location_reference]
        practitioner_reference = Reference.construct()
        practitioner_reference.reference = self._TEST_PRACTITIONER_REFERENCE
        fhir_practitioner_role.practitioner = practitioner_reference
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/practitioner-role-substitution-reference"
        reference = EnrolmentOfficerPractitionerConverter.build_fhir_resource_reference(
            self._TEST_SUBSTITUTION_OFFICER,
        )
        extension.valueReference = reference
        fhir_practitioner_role.extension = [extension]
        return fhir_practitioner_role

    def verify_fhir_instance(self, fhir_obj):
        self.assertIn(self._TEST_LOCATION_REFERENCE, fhir_obj.location[0].reference)
        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = EnrolmentOfficerPractitionerRoleConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_generic_type_code():
                self.assertEqual(self._TEST_OFFICER.code, identifier.value)
            elif code == R4IdentifierConfig.get_fhir_uuid_type_code():
                self.assertEqual(self._TEST_OFFICER.uuid, identifier.value)
        self.assertIn(self._TEST_PRACTITIONER_REFERENCE, fhir_obj.practitioner.reference)
        self.assertIn(self._TEST_SUBSTITUTION_OFFICER.uuid, fhir_obj.extension[0].valueReference.reference.split('Practitioner/')[1])
        self.assertEqual(1, len(fhir_obj.code))
        self.assertEqual(1, len(fhir_obj.code[0].coding))
        self.assertEqual("EO", fhir_obj.code[0].coding[0].code)
        self.assertEqual("Enrolment Officer",  fhir_obj.code[0].coding[0].display)
