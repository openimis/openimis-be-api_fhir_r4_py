from fhir.resources.R4B.practitionerrole import PractitionerRole
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.reference import Reference
from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import EnrolmentOfficerPractitionerConverter, EnrolmentOfficerPractitionerRoleConverter
from api_fhir_r4.tests import GenericTestMixin, EnrolmentOfficerPractitionerTestMixin, LocationTestMixin
from core.models import Officer
from location.test_helpers import create_test_village 
from core.test_helpers import create_test_officer

class EnrolmentOfficerPractitionerRoleTestMixin(GenericTestMixin):
    test_officer = None
    test_village = None
    test_substitution_officer = None
    _TEST_SUBSTITUTION_OFFICER_UUID = "f4bf924a-e2c9-46dc-9fa3-d54a1a67ea86"
    _TEST_OFFICER_UUID = "b578a621-0b11-4889-9454-a8e498c35dee"
    _TEST_SUBSTITUTION_OFFICER_CODE = "EOTESB"
    _TEST_OFFICER_CODE = "EOTEST"
    _TEST_PRACTITIONER_REFERENCE = None
    _TEST_VILLAGE_REFERENCE = 'Location/20fcfa89-149a-429e-bd26-b014b95fbb2d'
    _TEST_VILLAGE_UUID = "041890f3-d90b-46ca-8b25-56c3f8d60615"
    sub_str = {}
    
    def setUp(self):
        self.test_village = create_test_village()
        self.test_substitution_officer   = create_test_officer(custom_props ={
                "uuid": self._TEST_SUBSTITUTION_OFFICER_UUID,
                "code": self._TEST_SUBSTITUTION_OFFICER_CODE,
                "last_name": "Officer",
                "other_names": "Test",
                'location':self.test_village.parent.parent
        })
        self.test_officer= create_test_officer(custom_props ={                
                "uuid": self._TEST_OFFICER_UUID,
                "code": self._TEST_OFFICER_CODE,
                "substitution_officer": self.test_substitution_officer,
                "last_name": "Officer",
                "other_names": "Test",
                "validity_to": None,
                "audit_user_id": -1,
                'location':self.test_village.parent.parent})
        
        self._TEST_PRACTITIONER_REFERENCE = "Practitioner/" + str(self.test_officer.uuid)

        self.sub_str[self._TEST_SUBSTITUTION_OFFICER_UUID]=self.test_substitution_officer.uuid
        self.sub_str[self._TEST_OFFICER_UUID]=self.test_officer.uuid
        self.sub_str[self._TEST_VILLAGE_UUID]=self.test_village.uuid
        self.sub_str[self._TEST_VILLAGE_REFERENCE]="Location/" + str(self.test_village.uuid)
        self._TEST_VILLAGE_REFERENCE = "Location/" + str(self.test_village.uuid)




    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self.test_officer.substitution_officer.code, imis_obj.substitution_officer.code)
        self.assertEqual(self.test_village.code, imis_obj.location.code)

    def create_test_imis_instance(self):
        return self.test_officer

    def create_test_fhir_instance(self):
        self.create_test_imis_instance()
        fhir_practitioner_role = PractitionerRole.construct()
        identifiers = []
        code = EnrolmentOfficerPractitionerRoleConverter.build_fhir_identifier(
            self.test_officer.code,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        identifiers.append(code)
        location_reference = Reference.construct()
        location_reference.reference = self._TEST_VILLAGE_REFERENCE
        fhir_practitioner_role.location = [location_reference]
        practitioner_reference = Reference.construct()
        practitioner_reference.reference = self._TEST_PRACTITIONER_REFERENCE
        fhir_practitioner_role.practitioner = practitioner_reference
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/practitioner-role-substitution-reference"
        reference = EnrolmentOfficerPractitionerConverter.build_fhir_resource_reference(
            self.test_substitution_officer,
        )
        extension.valueReference = reference
        fhir_practitioner_role.extension = [extension]
        return fhir_practitioner_role

    def verify_fhir_instance(self, fhir_obj):
        return None #FIXME
        self.assertIn(str(self.test_village.uuid), fhir_obj.location[0].reference)
        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = EnrolmentOfficerPractitionerRoleConverter.get_first_coding_from_codeable_concept(
                identifier.type).code
            if code == R4IdentifierConfig.get_fhir_generic_type_code():
                self.assertEqual(self.test_officer.code, identifier.value)
            elif code == R4IdentifierConfig.get_fhir_uuid_type_code():
                self.assertEqual(str(self.test_officer.uuid), identifier.value)
        self.assertIn(str(self.test_officer.uuid), fhir_obj.practitioner.reference)
        self.assertIn(str(self.test_substitution_officer.uuid),
                      fhir_obj.extension[0].valueReference.reference.split('Practitioner/')[1])
        self.assertEqual(1, len(fhir_obj.code))
        self.assertEqual(1, len(fhir_obj.code[0].coding))
        self.assertEqual("EO", fhir_obj.code[0].coding[0].code)
        self.assertEqual("Enrolment Officer", fhir_obj.code[0].coding[0].display)
