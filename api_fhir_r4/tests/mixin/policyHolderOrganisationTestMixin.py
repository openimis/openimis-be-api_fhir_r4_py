from api_fhir_r4.tests import GenericTestMixin
from api_fhir_r4.utils import DbManagerUtils
from location.models import Location
from policyholder.models import PolicyHolder


class PolicyHolderOrganisationTestMixin(GenericTestMixin):
    _TEST_UUID = "1234-1234-1234-1234"
    _TEST_LEGAL_FORM = 2
    _TEST_ACTIVITY_CODE = 3
    _TEST_CODE = "ABCD"
    _TEST_TRADE_NAME = "Test test"
    _TEST_REGION = 'Tahida'
    _TEST_DISTRICT = 'Rajo'
    _TEST_MUNICIPALITY = 'Jaber'
    _TEST_VILLAGE = 'Utha'
    _TEST_CONTACT_NAME = "Name"
    _TEST_CONTACT_SURNAME = "Surname"
    _TEST_ADDRESS_LINE = "Test address 21"
    _TEST_EMAIL = "email@email.com"
    _TEST_PHONE = "111111111"
    _TEST_FAX = "123123123"
    _FIXED_TYPE = "bus"
    _FIXED_LOCATION_TYPE = "physical"

    def create_test_fhir_instance(self):
        NotImplementedError('PH Organization to_imis_obj() not implemented.')

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual(self._TEST_UUID, fhir_obj.id)

        actual_legal_form = next(iter(
            extension.valueCodeableConcept.coding[0].code for extension in fhir_obj.extension if
            "legal-form" in extension.url), None)
        self.assertEqual(str(self._TEST_LEGAL_FORM), actual_legal_form)

        actual_activity = next(iter(
            extension.valueCodeableConcept.coding[0].code for extension in fhir_obj.extension if
            "activity" in extension.url), None)
        self.assertEqual(str(self._TEST_ACTIVITY_CODE), actual_activity)

        actual_id_uuid = next(iter(
            identifier.value for identifier in fhir_obj.identifier if
            "UUID" == identifier.type.coding[0].code), None)
        self.assertEqual(self._TEST_UUID, actual_id_uuid)

        actual_id_code = next(iter(
            identifier.value for identifier in fhir_obj.identifier if
            "Code" == identifier.type.coding[0].code), None)
        self.assertEqual(self._TEST_CODE, actual_id_code)

        self.assertEqual(self._TEST_REGION, fhir_obj.address[0].state)
        self.assertEqual(self._TEST_DISTRICT, fhir_obj.address[0].district)
        self.assertEqual(self._TEST_VILLAGE, fhir_obj.address[0].city)
        self.assertEqual(self._TEST_ADDRESS_LINE, fhir_obj.address[0].line[0])

        self.assertEqual(self._FIXED_LOCATION_TYPE, fhir_obj.address[0].type)

        actual_municipality = next(iter(
            extension.valueString for extension in fhir_obj.address[0].extension if
            "municipality" in extension.url), None)
        self.assertEqual(self._TEST_MUNICIPALITY, actual_municipality)

        expected_contact_name = "%s %s" % (self._TEST_CONTACT_NAME, self._TEST_CONTACT_SURNAME)
        actual_contact_name = fhir_obj.contact[0]['name'].text
        self.assertEqual(expected_contact_name, actual_contact_name)

        actual_email = next(iter(telecom.value for telecom in fhir_obj.telecom if
                                 "email" == telecom.system), None)
        self.assertEqual(self._TEST_EMAIL, actual_email)

        actual_fax = next(iter(telecom.value for telecom in fhir_obj.telecom if
                               "fax" == telecom.system), None)
        self.assertEqual(self._TEST_FAX, actual_fax)

        actual_phone = next(iter(telecom.value for telecom in fhir_obj.telecom if
                                 "phone" == telecom.system), None)
        self.assertEqual(self._TEST_PHONE, actual_phone)
        self.assertEqual(self._FIXED_TYPE, fhir_obj.type[0].coding[0].code)

    def verify_imis_instance(self, imis_obj):
        NotImplementedError('PH Organization to_imis_obj() not implemented.')

    def create_test_imis_instance(self):
        location = DbManagerUtils.get_object_or_none(Location, name=self._TEST_VILLAGE, validity_to__isnull=True)

        return PolicyHolder(**{
            "uuid": self._TEST_UUID,
            "legal_form": self._TEST_LEGAL_FORM,
            "activity_code": self._TEST_ACTIVITY_CODE,
            "code": self._TEST_CODE,
            "trade_name": self._TEST_TRADE_NAME,
            "locations": location,
            "contact_name": {"name": self._TEST_CONTACT_NAME, "surname": self._TEST_CONTACT_SURNAME},
            "address": {"address": self._TEST_ADDRESS_LINE},
            "email": self._TEST_EMAIL,
            "fax": self._TEST_FAX,
            "phone": self._TEST_PHONE,
        })
