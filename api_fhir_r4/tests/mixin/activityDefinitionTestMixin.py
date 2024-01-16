import core
from fhir.resources.R4B.activitydefinition import ActivityDefinition
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.money import Money
from fhir.resources.R4B.timing import Timing, TimingRepeat
from fhir.resources.R4B.usagecontext import UsageContext
from medical.models import Service

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.mapping.activityDefinitionMapping import ServiceTypeMapping, UseContextMapping, WorkflowMapping, \
    VenueMapping
from api_fhir_r4.mapping.patientMapping import PatientCategoryMapping
from api_fhir_r4.tests import GenericTestMixin
from api_fhir_r4.tests.mixin import FhirConverterTestMixin
from api_fhir_r4.utils import TimeUtils


class ActivityDefinitionTestMixin(GenericTestMixin, FhirConverterTestMixin):
    _TEST_SERVICE_UUID = "1234-1234-1234"
    _TEST_SERVICE_CODE = "TEST"
    _TEST_SERVICE_NAME = "Test Service"
    _TEST_SERVICE_TYPE = Service.TYPE_CURATIVE
    _TEST_SERVICE_FREQUENCY = 1
    _TEST_SERVICE_CATEGORY = Service.CATEGORY_ANTENATAL
    _TEST_SERVICE_CARE_TYPE = Service.CARE_TYPE_BOTH
    _TEST_SERVICE_PATIENT_CATEGORY = 15  # 1 & 2 & 4 & 8 (all patient categories)
    _TEST_SERVICE_PRICE = 1.0
    _TEST_SERVICE_VALIDITY_FROM = TimeUtils.str_to_date("2020-01-01", "18:50:00")
    _TEST_SERVICE_LEVEL = "D"

    _TEST_ACTIVITY_DEFINITION_RESOURCE_TYPE = "ActivityDefinition"
    _TEST_ACTIVITY_DEFINITION_STATUS = "active"
    _TEST_ACTIVITY_DEFINITION_DATE = "2020-01-01T18:50:00"
    _TEST_ACTIVITY_DEFINITION_PRICE_EXTENSION_URL = \
        f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/unit-price"
    _TEST_ACTIVITY_DEFINITION_CURRENCY = core.currency
    _TEST_ACTIVITY_DEFINITION_TIMING_FREQUENCY = 1
    _TEST_ACTIVITY_DEFINITION_TIMING_UNIT = "d"

    _TEST_ACTIVITY_DEFINITION_LEVEL_EXT_URL = \
        F"{GeneralConfiguration.get_system_base_url()}StructureDefinition/activity-definition-level"
    _TEST_ACTIVITY_DEFINITION_LEVEL_CODING_TEXT = F"Day of service"
    _TEST_ACTIVITY_DEFINITION_LEVEL_CODING_SYSTEM = \
        F"{GeneralConfiguration.get_system_base_url()}ValueSet/activity-definition-level"

    def create_test_imis_instance(self):
        imis_service = Service()
        imis_service.uuid = self._TEST_SERVICE_UUID
        imis_service.code = self._TEST_SERVICE_CODE
        imis_service.name = self._TEST_SERVICE_NAME
        imis_service.type = self._TEST_SERVICE_TYPE
        imis_service.frequency = self._TEST_SERVICE_FREQUENCY
        imis_service.category = self._TEST_SERVICE_CATEGORY
        imis_service.care_type = self._TEST_SERVICE_CARE_TYPE
        imis_service.patient_category = self._TEST_SERVICE_PATIENT_CATEGORY
        imis_service.price = self._TEST_SERVICE_PRICE
        imis_service.validity_from = self._TEST_SERVICE_VALIDITY_FROM
        imis_service.level = self._TEST_SERVICE_LEVEL
        return imis_service

    def verify_imis_instance(self, imis_obj):
        self.assertEqual(self._TEST_SERVICE_UUID, imis_obj.uuid)
        self.assertEqual(self._TEST_SERVICE_CODE, imis_obj.code)
        self.assertEqual(self._TEST_SERVICE_NAME, imis_obj.name)
        self.assertEqual(self._TEST_SERVICE_TYPE, imis_obj.type)
        self.assertEqual(self._TEST_SERVICE_FREQUENCY, imis_obj.frequency)
        self.assertEqual(self._TEST_SERVICE_CATEGORY, imis_obj.category)
        self.assertEqual(self._TEST_SERVICE_CARE_TYPE, imis_obj.care_type)
        self.assertEqual(self._TEST_SERVICE_PATIENT_CATEGORY, imis_obj.patient_category)
        self.assertAlmostEqual(self._TEST_SERVICE_PRICE, imis_obj.price, places=2)
        self.assertEqual(self._TEST_SERVICE_VALIDITY_FROM, imis_obj.validity_from)
        self.assertEqual(self._TEST_SERVICE_LEVEL, imis_obj.level)

    def create_test_fhir_instance(self):
        PatientCategoryMapping.load()
        fhir_activity_definition = ActivityDefinition.construct()
        fhir_activity_definition.status = self._TEST_ACTIVITY_DEFINITION_STATUS
        fhir_activity_definition.resource_type = self._TEST_ACTIVITY_DEFINITION_RESOURCE_TYPE

        uuid_identifier = Identifier.construct()
        uuid_identifier.type = CodeableConcept.construct()
        uuid_coding = Coding.construct()
        uuid_coding.code = R4IdentifierConfig.get_fhir_uuid_type_code()
        uuid_coding.system = R4IdentifierConfig.get_fhir_identifier_type_system()
        uuid_identifier.type.coding = [uuid_coding]
        uuid_identifier.value = self._TEST_SERVICE_UUID

        sc_identifier = Identifier.construct()
        sc_identifier.type = CodeableConcept.construct()
        sc_coding = Coding.construct()
        sc_coding.code = R4IdentifierConfig.get_fhir_generic_type_code()
        sc_coding.system = R4IdentifierConfig.get_fhir_identifier_type_system()
        sc_identifier.type.coding = [sc_coding]
        sc_identifier.value = self._TEST_SERVICE_CODE

        fhir_activity_definition.identifier = [uuid_identifier, sc_identifier]

        fhir_activity_definition.date = self._TEST_ACTIVITY_DEFINITION_DATE
        fhir_activity_definition.id = self._TEST_SERVICE_UUID
        fhir_activity_definition.name = self._TEST_SERVICE_CODE
        fhir_activity_definition.title = self._TEST_SERVICE_NAME

        price_extension = Extension.construct()
        price_extension.url = self._TEST_ACTIVITY_DEFINITION_PRICE_EXTENSION_URL
        price_extension.valueMoney = Money.construct()
        price_extension.valueMoney.value = self._TEST_SERVICE_PRICE
        price_extension.valueMoney.currency = self._TEST_ACTIVITY_DEFINITION_CURRENCY

        level_extension = Extension(
                url=self._TEST_ACTIVITY_DEFINITION_LEVEL_EXT_URL,
                valueCodeableConcept=CodeableConcept(
                    coding=[Coding(
                        system=self._TEST_ACTIVITY_DEFINITION_LEVEL_CODING_SYSTEM,
                        code=self._TEST_SERVICE_LEVEL,
                        display=self._TEST_ACTIVITY_DEFINITION_LEVEL_CODING_TEXT
                    )],
                    text=self._TEST_ACTIVITY_DEFINITION_LEVEL_CODING_TEXT
                )
            )
        fhir_activity_definition.extension = [price_extension, level_extension]

        topic_codeable_concept = CodeableConcept.construct()
        topic_coding = Coding.construct()
        topic_coding.system = ServiceTypeMapping.fhir_service_type_coding[self._TEST_SERVICE_TYPE]["system"]
        topic_coding.code = ServiceTypeMapping.fhir_service_type_coding[self._TEST_SERVICE_TYPE]["code"]
        topic_coding.display = ServiceTypeMapping.fhir_service_type_coding[self._TEST_SERVICE_TYPE]["display"]
        topic_codeable_concept.coding = [topic_coding]
        fhir_activity_definition.topic = [topic_codeable_concept]

        timing = Timing.construct()
        timing.repeat = TimingRepeat.construct()
        timing.repeat.frequency = self._TEST_ACTIVITY_DEFINITION_TIMING_FREQUENCY
        timing.repeat.period = self._TEST_SERVICE_FREQUENCY
        timing.repeat.periodUnit = self._TEST_ACTIVITY_DEFINITION_TIMING_UNIT
        fhir_activity_definition.timingTiming = timing

        gender_usage_context = UsageContext.construct()
        gender_codeable_concept = CodeableConcept.construct()
        gender_coding = Coding.construct()
        gender_coding.system = UseContextMapping.fhir_use_context_coding["gender"]["system"]
        gender_coding.code = UseContextMapping.fhir_use_context_coding["gender"]["code"]
        gender_coding.display = UseContextMapping.fhir_use_context_coding["gender"]["display"]
        male_coding = Coding.construct()
        male_coding.system = PatientCategoryMapping.fhir_patient_category_coding["male"]["system"]
        male_coding.code = PatientCategoryMapping.fhir_patient_category_coding["male"]["code"]
        male_coding.display = PatientCategoryMapping.fhir_patient_category_coding["male"]["display"]
        female_coding = Coding.construct()
        female_coding.system = PatientCategoryMapping.fhir_patient_category_coding["female"]["system"]
        female_coding.code = PatientCategoryMapping.fhir_patient_category_coding["female"]["code"]
        female_coding.display = PatientCategoryMapping.fhir_patient_category_coding["female"]["display"]
        gender_codeable_concept.coding = [male_coding, female_coding]
        gender_codeable_concept.text = "Male or Female"
        gender_usage_context.valueCodeableConcept = gender_codeable_concept
        gender_usage_context.code = gender_coding

        age_usage_context = UsageContext.construct()
        age_codeable_concept = CodeableConcept.construct()
        age_coding = Coding.construct()
        age_coding.system = UseContextMapping.fhir_use_context_coding["age"]["system"]
        age_coding.code = UseContextMapping.fhir_use_context_coding["age"]["code"]
        age_coding.display = UseContextMapping.fhir_use_context_coding["age"]["display"]
        child_coding = Coding.construct()
        child_coding.system = PatientCategoryMapping.fhir_patient_category_coding["child"]["system"]
        child_coding.code = PatientCategoryMapping.fhir_patient_category_coding["child"]["code"]
        child_coding.display = PatientCategoryMapping.fhir_patient_category_coding["child"]["display"]
        adult_coding = Coding.construct()
        adult_coding.system = PatientCategoryMapping.fhir_patient_category_coding["adult"]["system"]
        adult_coding.code = PatientCategoryMapping.fhir_patient_category_coding["adult"]["code"]
        adult_coding.display = PatientCategoryMapping.fhir_patient_category_coding["adult"]["display"]
        age_codeable_concept.coding = [adult_coding, child_coding]
        age_codeable_concept.text = "Male or Female"
        age_usage_context.valueCodeableConcept = age_codeable_concept
        age_usage_context.code = age_coding

        venue_usage_context = UsageContext.construct()
        venue_codeable_concept = CodeableConcept.construct()
        venue_coding = Coding.construct()
        venue_coding.system = UseContextMapping.fhir_use_context_coding["venue"]["system"]
        venue_coding.code = UseContextMapping.fhir_use_context_coding["venue"]["code"]
        venue_coding.display = UseContextMapping.fhir_use_context_coding["venue"]["display"]
        amb_coding = Coding.construct()
        amb_coding.system = VenueMapping.fhir_venue_coding[Service.CARE_TYPE_OUT_PATIENT]["system"]
        amb_coding.code = VenueMapping.fhir_venue_coding[Service.CARE_TYPE_OUT_PATIENT]["code"]
        amb_coding.display = VenueMapping.fhir_venue_coding[Service.CARE_TYPE_OUT_PATIENT]["display"]
        imp_coding = Coding.construct()
        imp_coding.system = VenueMapping.fhir_venue_coding[Service.CARE_TYPE_IN_PATIENT]["system"]
        imp_coding.code = VenueMapping.fhir_venue_coding[Service.CARE_TYPE_IN_PATIENT]["code"]
        imp_coding.display = VenueMapping.fhir_venue_coding[Service.CARE_TYPE_IN_PATIENT]["display"]
        venue_codeable_concept.coding = [amb_coding, imp_coding]
        venue_codeable_concept.text = "ambulatory or IMP"
        venue_usage_context.valueCodeableConcept = venue_codeable_concept
        venue_usage_context.code = venue_coding

        workflow_usage_context = UsageContext.construct()
        workflow_codeable_concept = CodeableConcept.construct()
        workflow_coding = Coding.construct()
        workflow_coding.system = UseContextMapping.fhir_use_context_coding["workflow"]["system"]
        workflow_coding.code = UseContextMapping.fhir_use_context_coding["workflow"]["code"]
        workflow_coding.display = UseContextMapping.fhir_use_context_coding["workflow"]["display"]
        antenatal_coding = Coding.construct()
        antenatal_coding.system = WorkflowMapping.fhir_workflow_coding[Service.CATEGORY_ANTENATAL]["system"]
        antenatal_coding.code = WorkflowMapping.fhir_workflow_coding[Service.CATEGORY_ANTENATAL]["code"]
        antenatal_coding.display = WorkflowMapping.fhir_workflow_coding[Service.CATEGORY_ANTENATAL]["display"]
        workflow_codeable_concept.coding = [antenatal_coding]
        workflow_codeable_concept.text = "Antenatal"
        workflow_usage_context.valueCodeableConcept = workflow_codeable_concept
        workflow_usage_context.code = workflow_coding

        fhir_activity_definition.useContext = [gender_usage_context, age_usage_context,
                                               venue_usage_context, workflow_usage_context]

        return fhir_activity_definition

    def verify_fhir_instance(self, fhir_obj):
        self.assertIs(type(fhir_obj), ActivityDefinition)
        self.assertEqual(fhir_obj.resource_type, self._TEST_ACTIVITY_DEFINITION_RESOURCE_TYPE)
        self.assertEqual(fhir_obj.status, self._TEST_ACTIVITY_DEFINITION_STATUS)
        self.assertEqual(fhir_obj.id, self._TEST_SERVICE_UUID)
        self.assertEqual(fhir_obj.date, self._TEST_SERVICE_VALIDITY_FROM)
        self.assertEqual(len(fhir_obj.extension), 2)
        price_extension = fhir_obj.extension[0]
        self.assertIs(type(price_extension), Extension)
        self.assertEqual(price_extension.url, self._TEST_ACTIVITY_DEFINITION_PRICE_EXTENSION_URL)
        price_money = price_extension.valueMoney
        self.assertIs(type(price_money), Money)
        self.assertEqual(price_money.currency, self._TEST_ACTIVITY_DEFINITION_CURRENCY)
        self.assertAlmostEqual(price_money.value, self._TEST_SERVICE_PRICE, places=2)
        self.assertGreater(len(fhir_obj.identifier), 0)
        self.verify_fhir_identifier(fhir_obj, R4IdentifierConfig.get_fhir_uuid_type_code(), self._TEST_SERVICE_UUID)
        self.verify_fhir_identifier(fhir_obj, R4IdentifierConfig.get_fhir_generic_type_code(), self._TEST_SERVICE_CODE)
        timing_repeat = fhir_obj.timingTiming.repeat
        self.assertEqual(timing_repeat.frequency, self._TEST_ACTIVITY_DEFINITION_TIMING_FREQUENCY)
        self.assertEqual(timing_repeat.periodUnit, self._TEST_ACTIVITY_DEFINITION_TIMING_UNIT)
        self.assertEqual(timing_repeat.period, self._TEST_SERVICE_FREQUENCY)
        self.verify_fhir_use_context(fhir_obj, UseContextMapping.fhir_use_context_coding["gender"],
                                     [PatientCategoryMapping.fhir_patient_category_coding["male"],
                                      PatientCategoryMapping.fhir_patient_category_coding["female"]])
        self.verify_fhir_use_context(fhir_obj, UseContextMapping.fhir_use_context_coding["age"],
                                     [PatientCategoryMapping.fhir_patient_category_coding["adult"],
                                      PatientCategoryMapping.fhir_patient_category_coding["child"]])
        self.verify_fhir_use_context(fhir_obj, UseContextMapping.fhir_use_context_coding["workflow"],
                                     [WorkflowMapping.fhir_workflow_coding[self._TEST_SERVICE_CATEGORY]])
        self.verify_fhir_use_context(fhir_obj, UseContextMapping.fhir_use_context_coding["venue"],
                                     [VenueMapping.fhir_venue_coding[Service.CARE_TYPE_IN_PATIENT],
                                      VenueMapping.fhir_venue_coding[Service.CARE_TYPE_OUT_PATIENT]])

    def verify_fhir_use_context(self, fhir_obj, use_context_type, expected_use_contexts):
        if len(expected_use_contexts) > 0:
            use_contexts = [use_context for use_context in fhir_obj.useContext
                            if use_context.code.code == use_context_type["code"]]
            self.assertEqual(len(use_contexts), 1)
            self.assertEqual(use_contexts[0].code.display, use_context_type["display"])
            self.assertEqual(use_contexts[0].code.system, use_context_type["system"])
            codings = use_contexts[0].valueCodeableConcept.coding
            for use_context in expected_use_contexts:
                use_context_coding = [coding for coding in codings if coding.code == use_context["code"]]
                self.assertEqual(len(use_context_coding), 1)
                self.assertEqual(use_context_coding[0].display, use_context["display"])
                self.assertEqual(use_context_coding[0].system, use_context["system"])
