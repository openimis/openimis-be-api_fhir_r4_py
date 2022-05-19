from uuid import UUID

from insuree.models import Family, FamilyType
from location.models import Location

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import GroupConverter
from api_fhir_r4.mapping.groupMapping import GroupTypeMapping
from fhir.resources.extension import Extension
from fhir.resources.humanname import HumanName
from fhir.resources.identifier import Identifier
from fhir.resources.group import Group, GroupMember
from fhir.resources.reference import Reference
from api_fhir_r4.tests import GenericTestMixin

from insuree.test_helpers import create_test_insuree


class GroupTestMixin(GenericTestMixin):

    _TEST_LAST_NAME = "TEST_LAST_NAME"
    _TEST_OTHER_NAME = "TEST_OTHER_NAME"
    _TEST_UUID = "0a60f36c-62eb-11ea-bb93-93ec0339a3dd"
    _TEST_CHF_ID = "TestChfId1"
    _TEST_POVERTY_STATUS = False
    _TEST_FAMILY_TYPE = FamilyType.objects.get(code="H")
    _TEST_ADDRESS = "TEST_ADDRESS"
    _TEST_INSUREE_MOCKED_UUID = "7240daef-5f8f-4b0f-9042-b221e66f184a"
    _TEST_INSUREE_MOCKED_CHFID = "TestChfId1"
    _TEST_FAMILY_MOCKED_UUID = "8e33033a-9f60-43ad-be3e-3bfeb992aae5"
    _TEST_LOCATION_MUNICIPALITY_UUID = "a82f54bf-d983-4963-a279-490312a96344"
    _TEST_LOCATION_CODE = "RTDTMTVT"
    _TEST_LOCATION_UUID = "637f05cf-d8e8-4135-8250-7f01f01936bc"
    _TEST_LOCATION_NAME = "TEST_NAME"
    _TEST_LOCATION_TYPE = "V"

    def create_mocked_location(self):
        imis_location_region = Location()
        imis_location_region.code = "RT"
        imis_location_region.name = "Test"
        imis_location_region.type = "R"
        imis_location_region.save()

        imis_location_district = Location()
        imis_location_district.code = "RTDT"
        imis_location_district.name = "Test"
        imis_location_district.type = "D"
        imis_location_district.parent = imis_location_region
        imis_location_district.save()

        imis_location_municipality = Location()
        imis_location_municipality.code = "RTDTMT"
        imis_location_municipality.name = "Test"
        imis_location_municipality.type = "M"
        imis_location_municipality.parent = imis_location_district
        imis_location_municipality.uuid = self._TEST_LOCATION_MUNICIPALITY_UUID
        imis_location_municipality.save()

        imis_location = Location()
        imis_location.code = self._TEST_LOCATION_CODE
        imis_location.uuid = self._TEST_LOCATION_UUID
        imis_location.name = self._TEST_LOCATION_NAME
        imis_location.type = self._TEST_LOCATION_TYPE
        imis_location.parent = imis_location_municipality

        return imis_location

    def create_test_imis_instance(self):

        # create mocked insuree so as to create test family
        imis_mocked_insuree = create_test_insuree()
        imis_mocked_insuree.last_name = self._TEST_LAST_NAME
        imis_mocked_insuree.other_names = self._TEST_OTHER_NAME
        imis_mocked_insuree.uuid = self._TEST_INSUREE_MOCKED_UUID
        imis_mocked_insuree.chf_id = self._TEST_INSUREE_MOCKED_CHFID
        imis_mocked_insuree.save()

        # create mocked locations
        imis_location = self.create_mocked_location()
        imis_location.save()

        imis_family = Family()
        imis_family.head_insuree = imis_mocked_insuree
        imis_family.uuid = self._TEST_UUID
        imis_family.location = imis_location
        imis_family.address = self._TEST_ADDRESS
        imis_family.family_type = self._TEST_FAMILY_TYPE
        imis_family.poverty = self._TEST_POVERTY_STATUS
        imis_family.audit_user_id = -1
        imis_family.save()

        # save mocked insuree to the test family
        imis_mocked_insuree.family = imis_family
        imis_mocked_insuree.save()

        return imis_family

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_CHF_ID, imis_obj.head_insuree.chf_id)
        self.assertEqual(self._TEST_ADDRESS, imis_obj.address)
        self.assertEqual(self._TEST_POVERTY_STATUS, imis_obj.poverty)
        self.assertEqual(self._TEST_FAMILY_TYPE.code, imis_obj.family_type.code)

    def create_test_fhir_instance(self):
        # create mocked insuree so as to create test family
        imis_mocked_insuree = create_test_insuree(with_family=False)
        imis_mocked_insuree.uuid = self._TEST_INSUREE_MOCKED_UUID
        imis_mocked_insuree.chf_id = self._TEST_INSUREE_MOCKED_CHFID
        imis_mocked_insuree.save()

        # create mocked locations
        imis_location = self.create_mocked_location()
        imis_location.save()

        fhir_family = {}
        fhir_family['actual'] = True
        fhir_family['type'] = "Person"
        fhir_family = Group(**fhir_family)

        name = HumanName.construct()
        name.family = self._TEST_LAST_NAME
        name.given = [self._TEST_OTHER_NAME]
        name.use = "usual"

        identifiers = []
        chf_id = GroupConverter.build_fhir_identifier(
            self._TEST_CHF_ID,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )

        identifiers.append(chf_id)

        uuid = GroupConverter.build_fhir_identifier(
            self._TEST_UUID,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_uuid_type_code()
        )
        identifiers.append(uuid)

        fhir_family.identifier = identifiers

        fhir_family.quantity = 1
        fhir_family.name = imis_mocked_insuree.last_name

        members = []
        member = GroupMember.construct()
        reference = Reference.construct()
        reference.reference = f"Patient/{self._TEST_INSUREE_MOCKED_UUID}"
        reference.type = "Patient"
        member.entity = reference
        members.append(member)
        fhir_family.member = members

        # extensions for group
        fhir_family.extension = []

        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-poverty-status"
        extension.valueBoolean = self._TEST_POVERTY_STATUS
        fhir_family.extension = [extension]

        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-type"
        display = GroupTypeMapping.group_type[str(self._TEST_FAMILY_TYPE.code)]
        system = f"CodeSystem/group-type"
        extension.valueCodeableConcept = GroupConverter.build_codeable_concept(code=str(self._TEST_FAMILY_TYPE.code), system=system)
        if len(extension.valueCodeableConcept.coding) == 1:
            extension.valueCodeableConcept.coding[0].display = display
        fhir_family.extension.append(extension)

        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-address"
        family_address = GroupConverter.build_fhir_address(self._TEST_ADDRESS, "home", "physical")
        family_address.state = imis_location.parent.parent.parent.name
        family_address.district = imis_location.parent.parent.name

        # municipality extension
        extension_address = Extension.construct()
        extension_address.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-municipality"
        extension_address.valueString = imis_location.parent.name
        family_address.extension = [extension_address]

        # address location reference extension
        extension_address = Extension.construct()
        extension_address.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-location-reference"
        reference_location = Reference.construct()
        reference_location.reference = F"Location/{imis_location.uuid}"
        extension_address.valueReference = reference_location
        family_address.extension.append(extension_address)
        family_address.city = imis_location.name
        extension.valueAddress = family_address

        fhir_family.extension.append(extension)

        return fhir_family

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual('Person', fhir_obj.type)
        self.assertEqual(True, fhir_obj.actual)
        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = GroupConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_generic_type_code():
                self.assertEqual(self._TEST_CHF_ID, identifier.value)
            elif code == R4IdentifierConfig.get_fhir_uuid_type_code() and not isinstance(identifier.value, UUID):
                self.assertEqual(self._TEST_UUID, identifier.value)
        self.assertEqual(1, fhir_obj.quantity)
        self.assertEqual(1, len(fhir_obj.member))
        self.assertEqual(self._TEST_LAST_NAME, fhir_obj.name)
        self.assertEqual(3, len(fhir_obj.extension))
        for extension in fhir_obj.extension:
            self.assertTrue(isinstance(extension, Extension))
            if "group-address" in extension.url:
                no_of_extensions = len(extension.valueAddress.extension)
                self.assertEqual(2, no_of_extensions)
                self.assertEqual("home", extension.valueAddress.use)
                self.assertEqual(self._TEST_LOCATION_NAME, extension.valueAddress.city)
            if "group-poverty-status" in extension.url:
                self.assertEqual(self._TEST_POVERTY_STATUS, extension.valueBoolean)
            if "group-type" in extension.url:
                self.assertEqual(self._TEST_FAMILY_TYPE.code, extension.valueCodeableConcept.coding[0].code)
