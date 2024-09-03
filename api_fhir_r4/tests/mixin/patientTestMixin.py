from uuid import UUID

from insuree.models import Gender, Insuree, Profession
from location.models import Location
from location.test_helpers import create_test_location,create_test_village
from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig, R4MaritalConfig
from api_fhir_r4.converters import PatientConverter
from api_fhir_r4.mapping.patientMapping import PatientProfessionMapping
from fhir.resources.R4B.address import Address
from fhir.resources.R4B.attachment import Attachment
from fhir.resources.R4B.contactpoint import ContactPoint
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.humanname import HumanName
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.reference import Reference
from api_fhir_r4.models.imisModelEnums import ContactPointSystem, ContactPointUse
from api_fhir_r4.tests import GenericTestMixin
from api_fhir_r4.utils import TimeUtils

from insuree.test_helpers import create_test_insuree


class PatientTestMixin(GenericTestMixin):
    _TEST_LAST_NAME = "TEST_LAST_NAME"
    _TEST_OTHER_NAME = "TEST_OTHER_NAME"
    _TEST_IS_HEAD = False
    _TEST_INSUREE_DOB = "1990-03-24"
    _TEST_INSUREE_ID = 10000
    _TEST_INSUREE_UUID = "0a60f36c-62eb-11ea-bb93-93ec0339a3dd"
    _TEST_INSUREE_CHFID = "827192671"
    _TEST_PASSPORT = "TEST_PASSPORT"
    _TEST_GENDER_CODE = "M"
    _TEST_GENDER = None
    _TEST_PROFESSION = None
    _TEST_CARD_ISSUED = False
    _TEST_PHONE = "813-996-476"
    _TEST_EMAIL = "TEST@TEST.com"
    _TEST_ADDRESS = "TEST_ADDRESS"
    _TEST_INSUREE_MOCKED_UUID = "7240daef-5f8f-4b0f-9042-b221e66f184a"
    _TEST_GROUP_UUID = "8e33033a-9f60-43ad-be3e-3bfeb992aae5"
    _TEST_VILLAGE_CODE = "RTDTMTVT"
    _TEST_VILLAGE_UUID = "69a55f2d-ee34-4193-be0e-2b6a361797bd"
    _TEST_VILLAGE_NAME = "TEST_NAME"
    _TEST_PHOTO_FOLDER = "PhotoTest"
    _TEST_MOCKED_PHOTO = "TESTTEST"
    _TEST_MOCKED_PHOTO_TYPE = "png"
    _TEST_MOCKED_PHOTO_CREATION = "2021-03-27"
    _TEST_PHOTO_TITLE = "photo_test"
    test_insuree= None
    test_village= None
    test_region= None
    test_ward = None
    test_district = None
    sub_str = {}
    @classmethod
    def setUpTestData(cls):
        cls._TEST_GENDER = Gender()
        cls._TEST_GENDER.code = cls._TEST_GENDER_CODE
        cls._TEST_PROFESSION = Profession.objects.get(id=4)

        if cls.test_region is None:
            
            cls.test_village  =create_test_village( custom_props={"code":cls._TEST_VILLAGE_CODE,"name":cls._TEST_VILLAGE_NAME})
            cls.test_ward =cls.test_village.parent
            cls.test_region =cls.test_village.parent.parent.parent
            cls.test_district = cls.test_village.parent.parent
            
        cls.test_insuree = create_test_insuree(
            custom_props = {
                "last_name":cls._TEST_LAST_NAME,
                "other_names":cls._TEST_OTHER_NAME,
            "id" : cls._TEST_INSUREE_ID,
            "uuid" : cls._TEST_INSUREE_UUID,
            "chf_id" : cls._TEST_INSUREE_CHFID,
            "passport" : cls._TEST_PASSPORT,
            "dob" : TimeUtils.str_to_date(cls._TEST_INSUREE_DOB),
            "gender" : cls._TEST_GENDER,
            "marital": "D",
            "phone" : cls._TEST_PHONE,
            "email" : cls._TEST_EMAIL,
            "current_address" : cls._TEST_ADDRESS,
            "current_village" : cls.test_village,
            "profession" : cls._TEST_PROFESSION,
            "card_issued" : cls._TEST_CARD_ISSUED,
            }
        )
        
        cls.sub_str[cls._TEST_INSUREE_CHFID] = cls.test_insuree.chf_id
        cls.sub_str[cls._TEST_INSUREE_UUID] = cls.test_insuree.uuid
        cls.sub_str[cls._TEST_VILLAGE_UUID] = cls.test_village.uuid
        cls.sub_str[cls._TEST_GROUP_UUID] = cls.test_insuree.family.uuid
        cls._TEST_INSUREE_CHFID = cls.test_insuree.chf_id

        
            
    def create_test_imis_instance(self):
        return self.test_insuree

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_LAST_NAME, imis_obj.last_name)
        self.assertEqual(self._TEST_OTHER_NAME, imis_obj.other_names)
        self.assertEqual(self.test_insuree.chf_id, imis_obj.chf_id)
        expected_date = TimeUtils.str_to_date(self._TEST_INSUREE_DOB)
        self.assertEqual(expected_date, imis_obj.dob)
        self.assertEqual("D", imis_obj.marital)
        self.assertEqual(self._TEST_PHONE, imis_obj.phone)
        self.assertEqual(self._TEST_EMAIL, imis_obj.email)
        self.assertEqual(self._TEST_ADDRESS, imis_obj.current_address)
        self.assertEqual(self._TEST_IS_HEAD, imis_obj.head)
        self.assertEqual(self._TEST_PROFESSION.profession, imis_obj.profession.profession)
        self.assertEqual(self._TEST_CARD_ISSUED, imis_obj.card_issued)

    def create_test_fhir_instance(self):

        fhir_patient = Patient.construct()
        name = HumanName.construct()
        name.family = self.test_insuree.last_name
        name.given = [ self.test_insuree.other_names]
        name.use = "usual"
        fhir_patient.name = [name]
        identifiers = []
        chf_id = PatientConverter.build_fhir_identifier(
            self.test_insuree.chf_id,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )

        identifiers.append(chf_id)

        fhir_patient.identifier = identifiers
        fhir_patient.birthDate =  self.test_insuree.dob
        fhir_patient.gender = "male"
        fhir_patient.maritalStatus = PatientConverter.build_codeable_concept(
            R4MaritalConfig.get_fhir_divorced_code(),
            R4MaritalConfig.get_fhir_marital_status_system())
        telecom = []
        phone = PatientConverter.build_fhir_contact_point(
            self._TEST_PHONE,
            ContactPointSystem.PHONE,
            ContactPointUse.HOME
        )
        telecom.append(phone)
        email = PatientConverter.build_fhir_contact_point(
            self._TEST_EMAIL,
            ContactPointSystem.EMAIL,
            ContactPointUse.HOME
        )
        telecom.append(email)
        fhir_patient.telecom = telecom

        # family slice - required
        family_address = PatientConverter.build_fhir_address(self._TEST_ADDRESS, "home", "physical")
        family_address.state = self.test_village.parent.parent.parent.name
        family_address.district = self.test_village.parent.parent.name

        # municipality extension
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-municipality"
        extension.valueString = self.test_village.parent.name
        family_address.extension = [extension]

        # address location reference extension
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-location-reference"
        reference_location = Reference.construct()
        reference_location.reference = F"Location/{self.test_village.uuid}"
        extension.valueReference = reference_location
        family_address.extension.append(extension)

        family_address.city = self.test_village.name

        addresses = [family_address]

        # Commented out, as single address extension is required
        # # insuree slice
        # current_address = PatientConverter.build_fhir_address(self._TEST_ADDRESS, "temp", "physical")
        # current_address.state = self.test_village.parent.parent.parent.name
        # current_address.district = self.test_village.parent.parent.name
        #
        # # municipality extension
        # extension = Extension.construct()
        # extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-municipality"
        # extension.valueString = self.test_village.parent.name
        # current_address.extension = [extension]
        #
        # # address location reference extension
        # extension = Extension.construct()
        # extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-location-reference"
        # reference_location = Reference.construct()
        # reference_location.reference = F"Location/{self.test_village.uuid}"
        # extension.valueReference = reference_location
        # current_address.extension.append(extension)
        # current_address.city = self.test_village.name
        #
        # addresses.append(current_address)
        fhir_patient.address = addresses

        # test mocked_photo
        photo = Attachment.construct()
        photo.data = self._TEST_MOCKED_PHOTO
        photo.creation = self._TEST_MOCKED_PHOTO_CREATION
        photo.contentType = self._TEST_MOCKED_PHOTO_TYPE
        photo.title = self._TEST_PHOTO_TITLE
        if type(fhir_patient.photo) is not list:
            fhir_patient.photo = [photo]
        else:
            fhir_patient.photo.append(photo)

        # extensions
        fhir_patient.extension = []

        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-is-head"
        extension.valueBoolean = self._TEST_IS_HEAD
        fhir_patient.extension = [extension]

        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-card-issued"
        extension.valueBoolean = self._TEST_CARD_ISSUED
        fhir_patient.extension.append(extension)

        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-profession"
        PatientProfessionMapping.load()
        display = PatientProfessionMapping.patient_profession[str(self._TEST_PROFESSION.id)]
        system = "CodeSystem/patient-profession"
        extension.valueCodeableConcept = PatientConverter.build_codeable_concept(code=str(self._TEST_PROFESSION.id),
                                                                                 system=system)
        if len(extension.valueCodeableConcept.coding) == 1:
            extension.valueCodeableConcept.coding[0].display = display
        fhir_patient.extension.append(extension)

        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-group-reference"
        reference_group = Reference.construct()
        reference_group.reference = F"Group/{self.test_insuree.family.uuid}"
        extension.valueReference = reference_group
        fhir_patient.extension.append(extension)

        return fhir_patient

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual(1, len(fhir_obj.name))
        human_name = fhir_obj.name[0]
        self.assertTrue(isinstance(human_name, HumanName))
        self.assertEqual(self._TEST_OTHER_NAME, human_name.given[0])
        self.assertEqual(self._TEST_LAST_NAME, human_name.family)
        self.assertEqual("usual", human_name.use)
        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = PatientConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_generic_type_code():
                self.assertEqual(str(self.test_insuree.chf_id), identifier.value)
            elif code == R4IdentifierConfig.get_fhir_uuid_type_code() and not isinstance(identifier.value, UUID):
                self.assertEqual(str(self.test_insuree.uuid), identifier.value)
        self.assertEqual(self._TEST_INSUREE_DOB, fhir_obj.birthDate.isoformat())
        self.assertEqual("male", fhir_obj.gender)
        marital_code = PatientConverter.get_first_coding_from_codeable_concept(fhir_obj.maritalStatus).code
        self.assertEqual(R4MaritalConfig.get_fhir_divorced_code(), marital_code)
        self.assertEqual(2, len(fhir_obj.telecom))
        for telecom in fhir_obj.telecom:
            self.assertTrue(isinstance(telecom, ContactPoint))
            if telecom.system == "phone":
                self.assertEqual(self._TEST_PHONE, telecom.value)
            elif telecom.system == "email":
                self.assertEqual(self._TEST_EMAIL, telecom.value)
        for address in fhir_obj.address:
            self.assertTrue(isinstance(address, Address))
            if address.use == "home":
                no_of_extensions = len(address.extension)
                self.assertEqual(2, no_of_extensions)
                self.assertEqual("home", address.use)
                self.assertEqual(self._TEST_VILLAGE_NAME, address.city)
            elif address.use == "temp":
                self.assertEqual("temp", address.use)
                self.assertEqual(self._TEST_VILLAGE_NAME, address.city)
        for extension in fhir_obj.extension:
            self.assertTrue(isinstance(extension, Extension))
            if "patient-group-reference" in extension.url:
                self.assertIn(str(self.test_insuree.family.uuid), extension.valueReference.reference)
            if "patient-card-issue" in extension.url:
                self.assertEqual(self._TEST_CARD_ISSUED, extension.valueBoolean)
            if "patient-is-head" in extension.url:
                self.assertEqual(self._TEST_IS_HEAD, extension.valueBoolean)
            if "patient-profession" in extension.url:
                self.assertEqual(self._TEST_PROFESSION.profession, extension.valueCodeableConcept.coding[0].display)
