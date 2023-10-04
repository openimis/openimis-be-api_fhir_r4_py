import decimal
import re

from medical.models import Item

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import MedicationConverter
from api_fhir_r4.mapping.medicationMapping import ItemVenueTypeMapping
from api_fhir_r4.mapping.patientMapping import PatientCategoryMapping
from api_fhir_r4.tests import GenericTestMixin
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.money import Money
from fhir.resources.R4B.medication import Medication
from fhir.resources.R4B.ratio import Ratio
from fhir.resources.R4B.timing import Timing
from fhir.resources.R4B.quantity import Quantity
from fhir.resources.R4B.usagecontext import UsageContext


class MedicationTestMixin(GenericTestMixin):

    _TEST_MEDICATION_CODE = "TEST1"
    _TEST_MEDICATION_NAME = "TEST TABS 300MG"
    _TEST_MEDICATION_TYPE = "D"
    _TEST_MEDICATION_PACKAGE = "1000TABLETS"
    _TEST_MEDICATION_PRICE = 5.99
    _TEST_MEDICATION_CARE_TYPE = "B"
    _TEST_MEDICATION_FREQUENCY = 3
    _TEST_MEDICATION_PATIENT_CATEGORY = 15

    def create_test_imis_instance(self):
        imis_item = Item()
        imis_item.code = self._TEST_MEDICATION_CODE
        imis_item.name = self._TEST_MEDICATION_NAME
        imis_item.type = self._TEST_MEDICATION_TYPE
        imis_item.package = self._TEST_MEDICATION_PACKAGE
        imis_item.price = self._TEST_MEDICATION_PRICE
        imis_item.care_type = self._TEST_MEDICATION_CARE_TYPE
        imis_item.frequency = self._TEST_MEDICATION_FREQUENCY
        imis_item.patient_category = self._TEST_MEDICATION_PATIENT_CATEGORY
        return imis_item

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_MEDICATION_CODE, imis_obj.code)
        self.assertEqual(self._TEST_MEDICATION_NAME, imis_obj.name)
        self.assertEqual(self._TEST_MEDICATION_TYPE, imis_obj.type)
        self.assertEqual(self._TEST_MEDICATION_PACKAGE, imis_obj.package)
        self.assertAlmostEqual(decimal.Decimal(self._TEST_MEDICATION_PRICE), imis_obj.price, places=2)
        self.assertEqual(self._TEST_MEDICATION_CARE_TYPE, imis_obj.care_type)
        self.assertEqual(self._TEST_MEDICATION_FREQUENCY, imis_obj.frequency)
        self.assertEqual(self._TEST_MEDICATION_PATIENT_CATEGORY, imis_obj.patient_category)

    def create_test_fhir_instance(self):
        fhir_medication = Medication.construct()
        code = MedicationConverter.build_fhir_identifier(
            self._TEST_MEDICATION_CODE,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        identifiers = [code]
        fhir_medication.identifier = identifiers

        fhir_medication.form = MedicationConverter.build_codeable_concept("package", text=self._TEST_MEDICATION_PACKAGE)
        amount = MedicationConverter.split_package_amount(self._TEST_MEDICATION_PACKAGE)
        ratio = Ratio.construct()
        numerator = Quantity.construct()
        numerator.value = amount
        ratio.numerator = numerator
        fhir_medication.amount = ratio

        unit_price = MedicationConverter.build_fhir_unit_price_extension(self._TEST_MEDICATION_PRICE)
        fhir_medication.extension = [unit_price]

        medication_type = MedicationConverter.build_fhir_medication_type_extension(self._TEST_MEDICATION_TYPE)
        fhir_medication.extension.append(medication_type)

        medication_frequency = MedicationConverter.build_fhir_medication_frequency_extension(self._TEST_MEDICATION_FREQUENCY)
        fhir_medication.extension.append(medication_frequency)

        extension_usage = Extension.construct()
        extension_usage.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/medication-usage-context"

        # gender
        PatientCategoryMapping.load()
        male_flag = PatientCategoryMapping.imis_patient_category_flags["male"]
        female_flag = PatientCategoryMapping.imis_patient_category_flags["female"]
        extension = Extension.construct()
        extension.url = "Gender"
        administrative_system = "http://hl7.org/fhir/administrative-gender"
        extension.valueUsageContext = UsageContext.construct()
        extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
        if self._TEST_MEDICATION_PATIENT_CATEGORY & male_flag:
            coding_male = MedicationConverter._build_fhir_coding(code="male", display="Male", system=administrative_system)
            MedicationConverter._append_to_list_codeable_concept(extension, coding_male)
        if self._TEST_MEDICATION_PATIENT_CATEGORY & female_flag:
            coding_female = MedicationConverter._build_fhir_coding(code="female", display="Female", system=administrative_system)
            MedicationConverter._append_to_list_codeable_concept(extension, coding_female)
        system_gender = "http://terminology.hl7.org/CodeSystem/usage-context-type"
        extension.valueUsageContext.code = MedicationConverter._build_fhir_coding(code="gender", display="Gender", system=system_gender)
        gender = extension
        extension_usage.extension = [gender]

        # age type
        adult_flag = PatientCategoryMapping.imis_patient_category_flags["adult"]
        child_flag = PatientCategoryMapping.imis_patient_category_flags["child"]
        extension = Extension.construct()
        extension.url = "Age"
        usage_context_system = "http://terminology.hl7.org/CodeSystem/usage-context-type"
        age_type_system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/usage-context-age-type"
        extension.valueUsageContext = UsageContext.construct()
        extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
        if self._TEST_MEDICATION_PATIENT_CATEGORY & adult_flag:
            coding_adult = MedicationConverter._build_fhir_coding(code="adult", display="Adult", system=age_type_system)
            MedicationConverter._append_to_list_codeable_concept(extension, coding_adult)
        if self._TEST_MEDICATION_PATIENT_CATEGORY & child_flag:
            coding_child = MedicationConverter._build_fhir_coding(code="child", display="Child", system=age_type_system)
            MedicationConverter._append_to_list_codeable_concept(extension, coding_child)
        extension.valueUsageContext.code = MedicationConverter._build_fhir_coding(code="age", display="Age", system=usage_context_system)

        age = extension
        extension_usage.extension.append(age)

        code = ""
        if self._TEST_MEDICATION_CARE_TYPE == "O":
            code = "AMB"
        if self._TEST_MEDICATION_CARE_TYPE == "I":
            code = "IMP"
        if self._TEST_MEDICATION_CARE_TYPE == "B":
            code = "B"
        display = ItemVenueTypeMapping.item_venue_type[code]
        extension = Extension.construct()
        usage_context_system = "http://terminology.hl7.org/CodeSystem/usage-context-type"
        venue_system = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
        if self._TEST_MEDICATION_CARE_TYPE is not None:
            if code != "B":
                extension.url = "CareType"
                extension.valueUsageContext = UsageContext.construct()
                extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
                coding_venue = MedicationConverter._build_fhir_coding(code=code, display=display, system=venue_system)
                MedicationConverter._append_to_list_codeable_concept(extension, coding_venue)
            else:
                MedicationConverter.build_fhir_both_care_type(extension, venue_system)
            extension.valueUsageContext.code = MedicationConverter._build_fhir_coding(
                code="venue", display="Clinical Venue", system=usage_context_system)

        care_type = extension
        extension_usage.extension.append(care_type)
        fhir_medication.extension.append(extension_usage)

        fhir_medication.code = MedicationConverter.build_codeable_concept(self._TEST_MEDICATION_CODE, text=self._TEST_MEDICATION_NAME)
        fhir_medication.code.coding[0].system = "http://snomed.info/sct"
        fhir_medication.status = "active"
        return fhir_medication

    def verify_fhir_instance(self, fhir_obj):
        self.assertEqual(5, len(fhir_obj.extension))
        extension_unit_price = fhir_obj.extension[0].valueMoney
        self.assertTrue(isinstance(extension_unit_price, Money))
        self.assertAlmostEqual(decimal.Decimal(self._TEST_MEDICATION_PRICE), extension_unit_price.value, places=2)
        extension_medication_type = fhir_obj.extension[1].valueCodeableConcept
        self.assertTrue(isinstance(extension_medication_type, CodeableConcept))
        self.assertEqual(self._TEST_MEDICATION_TYPE, extension_medication_type.coding[0].code)
        extension_medication_frequency = fhir_obj.extension[2].valueTiming
        self.assertTrue(isinstance(extension_medication_frequency, Timing))
        self.assertEqual(self._TEST_MEDICATION_FREQUENCY, extension_medication_frequency.repeat.period)
        self.assertEqual(int(re.sub("[^0-9]", "", self._TEST_MEDICATION_PACKAGE)), fhir_obj.amount.numerator.value)
        self.assertEqual(self._TEST_MEDICATION_PACKAGE, fhir_obj.form.text)

        extension_usage_context = fhir_obj.extension[3].extension
        for ext in extension_usage_context:
            usage_context = ext.valueUsageContext
            self.assertTrue(isinstance(usage_context, UsageContext))
            # in every valueCodeableConcept 'coding' in that extensions (related to usage_context) should be two slices
            # because in that scenario we have all patient category type assigned
            self.assertEqual(2, len(ext.valueUsageContext.valueCodeableConcept.coding))

        for identifier in fhir_obj.identifier:
            self.assertTrue(isinstance(identifier, Identifier))
            code = MedicationConverter.get_first_coding_from_codeable_concept(identifier.type).code
            if code == R4IdentifierConfig.get_fhir_claim_admin_code_type():
                self.assertEqual(self._TEST_MEDICATION_CODE, identifier.value)
