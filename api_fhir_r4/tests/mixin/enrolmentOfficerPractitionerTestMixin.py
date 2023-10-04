from core.models import Officer
from django.utils.translation import gettext as _

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import ClaimAdminPractitionerConverter
from fhir.resources.R4B.contactpoint import ContactPoint
from fhir.resources.R4B.humanname import HumanName
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.practitioner import Practitioner, PractitionerQualification
from api_fhir_r4.models.imisModelEnums import ContactPointSystem, ContactPointUse
from api_fhir_r4.tests import GenericTestMixin
from api_fhir_r4.utils import TimeUtils


class EnrolmentOfficerPractitionerTestMixin(GenericTestMixin):

    _TEST_LAST_NAME = "Test"
    _TEST_OTHER_NAME = "Test"
    _TEST_DOB = "1990-03-24"
    _TEST_ID = 1
    _TEST_OFFICER_UUID = "b578a621-0b11-4889-9454-a8e498c35dee"
    _TEST_OFFICER_CODE = "EOTEST"
    _TEST_PHONE = "813-996-476"
    _TEST_EMAIL = "TEST@TEST.com"

    def create_test_imis_instance(self):
        imis_officer = Officer()
        imis_officer.last_name = self._TEST_LAST_NAME
        imis_officer.other_names = self._TEST_OTHER_NAME
        imis_officer.id = self._TEST_ID
        imis_officer.uuid = self._TEST_OFFICER_UUID
        imis_officer.code = self._TEST_OFFICER_CODE
        imis_officer.dob = TimeUtils.str_to_date(self._TEST_DOB)
        imis_officer.phone = self._TEST_PHONE
        imis_officer.email = self._TEST_EMAIL
        return imis_officer

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_LAST_NAME, imis_obj.last_name)
        self.assertEqual(self._TEST_OTHER_NAME, imis_obj.other_names)
        self.assertEqual(self._TEST_OFFICER_CODE, imis_obj.code)
        self.assertEqual(self._TEST_DOB+"T00:00:00", imis_obj.dob.isoformat())
        self.assertEqual(self._TEST_PHONE, imis_obj.phone)
        self.assertEqual(self._TEST_EMAIL, imis_obj.email)

    def create_test_fhir_instance(self):
        fhir_practitioner = Practitioner.construct()
        name = HumanName.construct()
        name.family = self._TEST_LAST_NAME
        name.given = [self._TEST_OTHER_NAME]
        name.use = "usual"
        fhir_practitioner.name = [name]
        identifiers = []
        code = ClaimAdminPractitionerConverter.build_fhir_identifier(
            self._TEST_OFFICER_CODE,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        identifiers.append(code)
        fhir_practitioner.identifier = identifiers
        fhir_practitioner.birthDate = self._TEST_DOB
        telecom = []
        phone = ClaimAdminPractitionerConverter.build_fhir_contact_point(
            self._TEST_PHONE, ContactPointSystem.PHONE,
            ContactPointUse.HOME
        )
        telecom.append(phone)
        email = ClaimAdminPractitionerConverter.build_fhir_contact_point(
            self._TEST_EMAIL,
            ContactPointSystem.EMAIL,
            ContactPointUse.HOME
        )
        telecom.append(email)
        fhir_practitioner.telecom = telecom

        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/practitioner-qualification-type"
        qualification = PractitionerQualification.construct()
        qualification.code = ClaimAdminPractitionerConverter.build_codeable_concept(
            system=system,
            code="EO",
            display=_("Enrolment Officer")
        )
        fhir_practitioner.qualification = [qualification]

        return fhir_practitioner

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual(1, len(fhir_obj.name))
        human_name = fhir_obj.name[0]
        self.assertTrue(isinstance(human_name, HumanName))
        self.assertEqual(self._TEST_OTHER_NAME, human_name.given[0])
        self.assertEqual(self._TEST_LAST_NAME, human_name.family)
        self.assertEqual("usual", human_name.use)
        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = ClaimAdminPractitionerConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_generic_type_code():
                self.assertEqual(self._TEST_OFFICER_CODE, identifier.value)
            elif code == R4IdentifierConfig.get_fhir_uuid_type_code():
                self.assertEqual(self._TEST_OFFICER_UUID, identifier.value)
        self.assertEqual(self._TEST_DOB, fhir_obj.birthDate.isoformat())
        self.assertEqual(2, len(fhir_obj.telecom))
        for telecom in fhir_obj.telecom:
            self.assertTrue(isinstance(telecom, ContactPoint))
            if telecom.system == "phone":
                self.assertEqual(self._TEST_PHONE, telecom.value)
            elif telecom.system == "email":
                self.assertEqual(self._TEST_EMAIL, telecom.value)
        self.assertEqual(1, len(fhir_obj.qualification))
        self.assertEqual("EO", fhir_obj.qualification[0].code.coding[0].code)
        self.assertEqual("Enrolment Officer", fhir_obj.qualification[0].code.coding[0].display)
