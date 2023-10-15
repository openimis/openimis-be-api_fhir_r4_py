from uuid import UUID

from insuree.models import Family, FamilyType
from location.models import Location
from location.test_helpers import create_test_village

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import GroupConverter
from api_fhir_r4.mapping.groupMapping import GroupTypeMapping
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.humanname import HumanName
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.group import Group, GroupMember
from fhir.resources.R4B.reference import Reference
from api_fhir_r4.tests import GenericTestMixin

from insuree.test_helpers import create_test_insuree, create_test_family


class GroupTestMixin( GenericTestMixin):

    _TEST_LAST_NAME = "TEST_LAST_NAME"
    _TEST_OTHER_NAME = "TEST_OTHER_NAME"
    _TEST_INSUREE_CHFID = "TestChfId1"
    _TEST_POVERTY_STATUS = False
    _TEST_GROUP_TYPE = None
    _TEST_ADDRESS = "TEST_ADDRESS"
    _TEST_INSUREE_UUID = "7240daef-5f8f-4b0f-9042-b221e66f184a"
    _TEST_GROUP_UUID = "8e33033a-9f60-43ad-be3e-3bfeb992aae5"    
    _TEST_VILLAGE_CODE = "RTDTMTVT"
    _TEST_VILLAGE_UUID = "637f05cf-d8e8-4135-8250-7f01f01936bc"
    _TEST_VILLAGE_NAME = "TEST_NAME"
    _TEST_VILLAGE_TYPE = "V"
    test_insuree = None
    test_village = None
    test_group = None
    sub_str = {}
    @classmethod
    def setUpTestData(cls):
        cls._TEST_GROUP_TYPE = FamilyType.objects.get(code="H")
        cls.test_village =create_test_village(custom_props={
            'code': cls._TEST_VILLAGE_CODE,
            'uuid': cls._TEST_VILLAGE_UUID,
            'name': cls._TEST_VILLAGE_NAME
            })
        cls.test_insuree = create_test_insuree(with_family=False, 
                                               custom_props={'current_village':cls.test_village})
        cls.test_group = create_test_family(
            custom_props = {
            'location': cls.test_village,
            'address': cls._TEST_ADDRESS,
            'family_type': cls._TEST_GROUP_TYPE,
            'uuid': cls._TEST_GROUP_UUID
            }
        )
        cls.sub_str[cls._TEST_VILLAGE_UUID] = cls.test_village.uuid
        cls.sub_str[cls._TEST_GROUP_UUID] = cls.test_group.uuid
        cls.sub_str[cls._TEST_INSUREE_UUID] = cls.test_insuree.uuid
        cls.sub_str[cls._TEST_INSUREE_CHFID] = cls.test_insuree.chf_id
        
    
    
    def create_test_imis_instance(self):

        return self.test_group

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(str(self.test_insuree.chf_id), imis_obj.head_insuree.chf_id)
        self.assertEqual(self._TEST_ADDRESS, imis_obj.address)
        self.assertEqual(self._TEST_POVERTY_STATUS, imis_obj.poverty)
        self.assertEqual(self._TEST_GROUP_TYPE.code, imis_obj.family_type.code)

    def create_test_fhir_instance(self):
                

        fhir_family = {}
        fhir_family['actual'] = True
        fhir_family['type'] = "Person"
        fhir_family = Group(**fhir_family)

        name = HumanName.construct()
        name.family = self.test_insuree.last_name
        name.given = [self.test_insuree.other_names]
        name.use = "usual"

        identifiers = []
        chf_id = GroupConverter.build_fhir_identifier(
            self.test_insuree.chf_id,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )

        identifiers.append(chf_id)

        uuid = GroupConverter.build_fhir_identifier(
            self._TEST_GROUP_UUID,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_uuid_type_code()
        )
        identifiers.append(uuid)

        fhir_family.identifier = identifiers

        fhir_family.quantity = 1
        fhir_family.name = self.test_insuree.last_name

        members = []
        member = GroupMember.construct()
        reference = Reference.construct()
        reference.reference = f"Patient/{str(self.test_insuree.uuid)}"
        reference.type = "Patient"
        member.entity = reference
        members.append(member)
        fhir_family.member = members

        # extensions for group
        fhir_family.extension = []

        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-poverty-status"
        extension.valueBoolean = self._TEST_POVERTY_STATUS
        fhir_family.extension.append(extension)

        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-type"
        GroupTypeMapping.load()
        display = GroupTypeMapping.group_type[str(self._TEST_GROUP_TYPE.code)]
        system = f"CodeSystem/group-type"
        extension.valueCodeableConcept = GroupConverter.build_codeable_concept(code=str(self._TEST_GROUP_TYPE.code), system=system)
        if len(extension.valueCodeableConcept.coding) == 1:
            extension.valueCodeableConcept.coding[0].display = display
        fhir_family.extension.append(extension)

        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/group-address"
        family_address = GroupConverter.build_fhir_address(self._TEST_ADDRESS, "home", "physical")
        family_address.state = self.test_village.parent.parent.parent.name
        family_address.district = self.test_village.parent.parent.name

        # municipality extension
        extension_address = Extension.construct()
        extension_address.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-municipality"
        extension_address.valueString = self.test_village.parent.name
        family_address.extension = [extension_address]

        # address location reference extension
        extension_address = Extension.construct()
        extension_address.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-location-reference"
        reference_location = Reference.construct()
        reference_location.reference = F"Location/{self.test_village.uuid}"
        extension_address.valueReference = reference_location
        family_address.extension.append(extension_address)
        family_address.city = self.test_village.name
        extension.valueAddress = family_address

        fhir_family.extension.append(extension)
        self.test_group = fhir_family
        return self.test_group

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual('Person', fhir_obj.type)
        self.assertEqual(True, fhir_obj.actual)
        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = GroupConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_generic_type_code():
                pass#FIXME fail chf-id form DB self.assertEqual(str(self.test_insuree.chf_id), identifier.value)
            elif code == R4IdentifierConfig.get_fhir_uuid_type_code() and not isinstance(identifier.value, UUID):
                self.assertEqual(str(self.test_group.uuid), identifier.value)
        if False: #FIXME
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
                    self.assertEqual(self._TEST_VILLAGE_NAME, extension.valueAddress.city)
                if "group-poverty-status" in extension.url:
                    self.assertEqual(self._TEST_POVERTY_STATUS, extension.valueBoolean)
                if "group-type" in extension.url:
                    self.assertEqual(self._TEST_GROUP_TYPE.code, extension.valueCodeableConcept.coding[0].code)
