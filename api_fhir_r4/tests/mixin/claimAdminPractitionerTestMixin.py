from claim.models import ClaimAdmin
from django.utils.translation import gettext as _

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import ClaimAdminPractitionerConverter, HealthFacilityOrganisationConverter
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.extension import Extension
from fhir.resources.humanname import HumanName
from fhir.resources.identifier import Identifier
from fhir.resources.practitioner import Practitioner, PractitionerQualification
from fhir.resources.reference import Reference
from api_fhir_r4.models.imisModelEnums import ContactPointSystem, ContactPointUse
from api_fhir_r4.tests import GenericTestMixin, LocationTestMixin
from api_fhir_r4.utils import TimeUtils
from location.models import HealthFacility


class ClaimAdminPractitionerTestMixin(GenericTestMixin):

    _TEST_LAST_NAME = "Smith"
    _TEST_OTHER_NAME = "John"
    _TEST_DOB = "1990-03-24"
    _TEST_ID = 1
    _TEST_UUID = "254f6268-964b-4d8d-aa26-20081f22235e"
    _TEST_CODE = "1234abcd"
    _TEST_PHONE = "813-996-476"
    _TEST_EMAIL = "TEST@TEST.com"
    _TEST_FAX = "1-408-999 8888"
    _TEST_ADDRESS = "TEST_ADDRESS"

    _TEST_HF_ID = 10000
    _TEST_HF_UUID = "6d0eea8c-62eb-11ea-94d6-c36229a16c2f"
    _TEST_HF_CODE = "12345678"
    _TEST_HF_NAME = "TEST_NAME"
    _TEST_HF_LEVEL = "H"
    _TEST_HF_LEGAL_FORM = "G"

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
        imis_claim_admin = ClaimAdmin()
        imis_claim_admin.last_name = self._TEST_LAST_NAME
        imis_claim_admin.other_names = self._TEST_OTHER_NAME
        imis_claim_admin.id = self._TEST_ID
        imis_claim_admin.uuid = self._TEST_UUID
        imis_claim_admin.code = self._TEST_CODE
        imis_claim_admin.dob = TimeUtils.str_to_date(self._TEST_DOB)
        imis_claim_admin.phone = self._TEST_PHONE
        imis_claim_admin.email_id = self._TEST_EMAIL
        hf = self.create_test_health_facility()
        imis_claim_admin.health_facility_id = hf.id
        imis_claim_admin.health_facility = hf
        imis_claim_admin.health_facility_code = hf.code
        return imis_claim_admin

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_LAST_NAME, imis_obj.last_name)
        self.assertEqual(self._TEST_OTHER_NAME, imis_obj.other_names)
        self.assertEqual(self._TEST_CODE, imis_obj.code)
        self.assertEqual(self._TEST_DOB+"T00:00:00", imis_obj.dob.isoformat())
        self.assertEqual(self._TEST_PHONE, imis_obj.phone)
        self.assertEqual(self._TEST_EMAIL, imis_obj.email_id)
        # we are not checking the extension as it's optional and the health facility
        # membership should be changed otherwise

    def create_test_fhir_instance(self):
        fhir_practitioner = Practitioner.construct()
        name = HumanName.construct()
        name.family = self._TEST_LAST_NAME
        name.given = [self._TEST_OTHER_NAME]
        name.use = "usual"
        fhir_practitioner.name = [name]
        identifiers = []
        code = ClaimAdminPractitionerConverter.build_fhir_identifier(
            self._TEST_CODE,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        identifiers.append(code)
        fhir_practitioner.identifier = identifiers
        fhir_practitioner.birthDate = self._TEST_DOB
        telecom = []
        phone = ClaimAdminPractitionerConverter.build_fhir_contact_point(
            self._TEST_PHONE,
            ContactPointSystem.PHONE,
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
            code="CA",
            display=_("Claim Administrator")
        )
        fhir_practitioner.qualification = [qualification]
        
        organization_reference = Reference.construct()
        resource_type = 'Organization'
        resource_id = '12345678'

        organization_reference.type = resource_type
        organization_reference.identifier = HealthFacilityOrganisationConverter.build_fhir_identifier(
            self._TEST_HF_CODE,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code())
        organization_reference.reference = f'{resource_type}/{resource_id}'
        organization_reference.display = resource_id

        extension_organization = Extension.construct()
        extension_organization.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/reference"
        extension_organization.valueReference = organization_reference
        fhir_practitioner.extension = [extension_organization]

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
                self.assertEqual(self._TEST_CODE, identifier.value)
            elif code == R4IdentifierConfig.get_fhir_uuid_type_code():
                self.assertEqual(self._TEST_UUID, identifier.value)
        self.assertEqual(self._TEST_DOB, fhir_obj.birthDate.isoformat())
        self.assertEqual(2, len(fhir_obj.telecom))
        for telecom in fhir_obj.telecom:
            self.assertTrue(isinstance(telecom, ContactPoint))
            if telecom.system == "phone":
                self.assertEqual(self._TEST_PHONE, telecom.value)
            elif telecom.system == "email":
                self.assertEqual(self._TEST_EMAIL, telecom.value)
        self.assertEqual(1, len(fhir_obj.qualification))
        self.assertEqual("CA", fhir_obj.qualification[0].code.coding[0].code)
        self.assertEqual("Claim Administrator", fhir_obj.qualification[0].code.coding[0].display)
        self.assertEqual("12345678", fhir_obj.extension[0].valueReference.display)
