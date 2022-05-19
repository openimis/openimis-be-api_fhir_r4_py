from django.utils.translation import gettext as _
from medical.models import Item
from api_fhir_r4.converters import R4IdentifierConfig, BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.models import UsageContextV2 as UsageContext
from api_fhir_r4.mapping.medicationMapping import ItemTypeMapping, ItemVenueTypeMapping, ItemContextlevel
from api_fhir_r4.mapping.patientMapping import PatientCategoryMapping
from fhir.resources.medication import Medication as FHIRMedication
from fhir.resources.extension import Extension
from fhir.resources.money import Money
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.quantity import Quantity
from fhir.resources.ratio import Ratio
from fhir.resources.timing import Timing, TimingRepeat
from django.utils.translation import gettext
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.utils import DbManagerUtils
from api_fhir_r4.configurations import GeneralConfiguration
import core


class MedicationConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_medication, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_medication = FHIRMedication.construct()
        cls.build_fhir_pk(fhir_medication, imis_medication, reference_type)
        cls.build_fhir_identifiers(fhir_medication, imis_medication)
        cls.build_fhir_package_form(fhir_medication, imis_medication)
        cls.build_fhir_package_amount(fhir_medication, imis_medication)
        cls.build_fhir_medication_extension(fhir_medication, imis_medication)
        cls.build_fhir_code(fhir_medication, imis_medication)
        cls.build_fhir_status(fhir_medication, imis_medication)
        cls.build_fhir_level(fhir_medication, imis_medication)
        return fhir_medication

    @classmethod
    def to_imis_obj(cls, fhir_medication, audit_user_id):
        errors = []
        fhir_medication = FHIRMedication(**fhir_medication)
        imis_medication = Item()
        imis_medication.audit_user_id = audit_user_id
        cls.build_imis_identifier(imis_medication, fhir_medication, errors)
        cls.build_imis_item_code(imis_medication, fhir_medication, errors)
        cls.build_imis_item_name(imis_medication, fhir_medication, errors)
        cls.build_imis_item_package(imis_medication, fhir_medication, errors)
        cls.build_imis_item_extension(imis_medication, fhir_medication, errors)
        cls.check_errors(errors)
        return imis_medication

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

    @classmethod
    def get_reference_obj_uuid(cls, imis_medication: Item):
        return imis_medication.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_medication: Item):
        return imis_medication.id

    @classmethod
    def get_reference_obj_code(cls, imis_medication: Item):
        return imis_medication.code

    @classmethod
    def get_fhir_resource_type(cls):
        return FHIRMedication

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_medication_code = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Item, uuid=imis_medication_code)

    @classmethod
    def build_fhir_identifiers(cls, fhir_medication, imis_medication):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_medication)
        fhir_medication.identifier = identifiers

    @classmethod
    def build_imis_identifier(cls, imis_medication, fhir_medication, errors):
        value = cls.get_fhir_identifier_by_code(fhir_medication.identifier,
                                                R4IdentifierConfig.get_fhir_uuid_type_code())
        if value:
            imis_medication.code = value
        cls.valid_condition(imis_medication.code is None, gettext('Missing the item code'), errors)

    @classmethod
    def build_fhir_package_form(cls, fhir_medication, imis_medication):
        # TODO - Split medical item ItemPackage into ItemForm and ItemAmount => openIMIS side
        if imis_medication.package:
            codeable = CodeableConcept.construct()
            codeable.text = imis_medication.package.lstrip()
            fhir_medication.form = codeable

    @classmethod
    def split_package_form(cls, form):
        form = form.lstrip()
        if " " not in form:
            return form
        if " " in form:
            form = form.split(' ', 1)
            form = form[1]
            return form

    @classmethod
    def build_fhir_package_amount(cls, fhir_medication, imis_medication):
        # TODO - Split medical item ItemPackage into ItemForm and ItemAmount => openIMIS side
        if imis_medication.package:
            amount = cls.split_package_amount(imis_medication.package)
            ratio = Ratio.construct()
            numerator = Quantity.construct()
            numerator.value = amount
            ratio.numerator = numerator
            fhir_medication.amount = ratio

    @classmethod
    def split_package_amount(cls, amount):
        amount = amount.lstrip()
        if " " not in amount:
            return None
        if " " in amount:
            amount = amount.split(' ', 1)
            amount = amount[0]
            return int(amount)

    @classmethod
    def build_fhir_medication_extension(cls, fhir_medication, imis_medication):
        cls.build_fhir_unit_price(fhir_medication, imis_medication)
        cls.build_fhir_medication_type(fhir_medication, imis_medication)
        cls.build_fhir_medication_frequency(fhir_medication, imis_medication)
        cls.build_fhir_use_context(fhir_medication, imis_medication)

    @classmethod
    def build_fhir_unit_price(cls, fhir_medication, imis_medication):
        unit_price = cls.build_fhir_unit_price_extension(imis_medication.price)
        if type(fhir_medication.extension) is not list:
            fhir_medication.extension = [unit_price]
        else:
            fhir_medication.extension.append(unit_price)

    @classmethod
    def build_fhir_unit_price_extension(cls, value):
        extension = Extension.construct()
        money = Money.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/unit-price"
        extension.valueMoney = money
        extension.valueMoney.value = value
        if hasattr(core, 'currency'):
            extension.valueMoney.currency = core.currency
        return extension

    @classmethod
    def build_fhir_medication_type(cls, fhir_medication, imis_medication):
        medication_type = cls.build_fhir_medication_type_extension(imis_medication.type)
        if type(fhir_medication.extension) is not list:
            fhir_medication.extension = [medication_type]
        else:
            fhir_medication.extension.append(medication_type)

    @classmethod
    def build_fhir_medication_type_extension(cls, value):
        extension = Extension.construct()
        display = ItemTypeMapping.item_type[value]
        system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/medication-item-type"
        coding = cls.build_codeable_concept(code=value, system=system, display=_(display))
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/medication-type"
        extension.valueCodeableConcept = coding
        return extension

    @classmethod
    def build_fhir_medication_frequency(cls, fhir_medication, imis_medication):
        if imis_medication.frequency:
            medication_frequency = cls.build_fhir_medication_frequency_extension(imis_medication.frequency)
            if type(fhir_medication.extension) is not list:
                fhir_medication.extension = [medication_frequency]
            else:
                fhir_medication.extension.append(medication_frequency)

    @classmethod
    def build_fhir_medication_frequency_extension(cls, value):
        # TODO: Is this ok? Value is assigned to period instead of frequency
        extension = Extension.construct()
        timing = Timing.construct()
        timing_repeat = TimingRepeat.construct()
        timing_repeat.frequency = 1
        timing_repeat.period = str(value)
        timing_repeat.periodUnit = 'd'
        timing.repeat = timing_repeat
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/medication-frequency"
        extension.valueTiming = timing
        return extension

    @classmethod
    def build_fhir_code(cls, fhir_medication, imis_medication):
        codeable = CodeableConcept.construct()
        codeable.text = imis_medication.name
        fhir_medication.code = codeable

    @classmethod
    def build_fhir_status(cls, fhir_medication, imis_medication):
        fhir_medication.status = "active"

    @classmethod
    def build_imis_item_code(cls, imis_medication, fhir_medication, errors):
        item_code = cls.get_fhir_identifier_by_code(fhir_medication.identifier,
                                                    R4IdentifierConfig.get_fhir_generic_type_code())
        if not cls.valid_condition(item_code is None,
                                   gettext('Missing medication `item_code` attribute'), errors):
            imis_medication.code = item_code

    @classmethod
    def build_imis_item_name(cls, imis_medication, fhir_medication, errors):
        if not cls.valid_condition(fhir_medication.code is None,
                                   gettext('Missing medication `item_name` attribute'), errors):
            item_name = fhir_medication.code.text
            imis_medication.name = item_name

    @classmethod
    def build_imis_item_package(cls, imis_medication, fhir_medication, errors):
        if not cls.valid_condition(fhir_medication.form is None,
                                   gettext('Missing medication `form` and `amount` attribute'), errors):
            form = fhir_medication.form.text
            imis_medication.package = form

    @classmethod
    def build_imis_item_extension(cls, imis_medication, fhir_medication, errors):
        extensions = fhir_medication.extension
        for extension in extensions:
            if "unit-price" in extension.url:
                cls.build_imis_unit_price(imis_medication, extension)
            if "medication-type" in extension.url:
                cls.build_imis_medication_type(imis_medication, extension)
            if "medication-frequency" in extension.url:
                cls.build_imis_medication_frequency(imis_medication, extension)
            if "medication-usage-context" in extension.url:
                cls.build_imis_item_usage_context(imis_medication, extension)

    @classmethod
    def build_fhir_use_context(cls, fhir_medication, imis_medication):
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/medication-usage-context"
        gender = cls.build_fhir_gender(imis_medication)
        # check only the first to be sure if we have list, the
        # next ones for sure will be a part of list of extensions
        if type(extension.extension) is not list:
            extension.extension = [gender]
        else:
            extension.extension.append(gender)

        age = cls.build_fhir_age(imis_medication)
        extension.extension.append(age)

        care_type = cls.build_fhir_care_type(imis_medication)
        if care_type:
            extension.extension.append(care_type)
        fhir_medication.extension.append(extension)

    @classmethod
    def build_fhir_gender(cls, imis_medication):
        male_flag = PatientCategoryMapping.imis_patient_category_flags["male"]
        female_flag = PatientCategoryMapping.imis_patient_category_flags["female"]
        extension = Extension.construct()
        extension.url = "Gender"
        administrative_system = "http://hl7.org/fhir/administrative-gender"
        extension.valueUsageContext = UsageContext.construct()
        extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
        if imis_medication.patient_category & male_flag:
            coding_male = cls._build_fhir_coding(code="male", display="Male", system=administrative_system)
            cls._append_to_list_codeable_concept(extension, coding_male)
        if imis_medication.patient_category & female_flag:
            coding_female = cls._build_fhir_coding(code="female", display="Female", system=administrative_system)
            cls._append_to_list_codeable_concept(extension, coding_female)
        system_gender = "http://terminology.hl7.org/CodeSystem/usage-context-type"
        extension.valueUsageContext.code = cls._build_fhir_coding(code="gender", display="Gender", system=system_gender)
        return extension

    @classmethod
    def build_fhir_age(cls, imis_medication):
        adult_flag = PatientCategoryMapping.imis_patient_category_flags["adult"]
        child_flag = PatientCategoryMapping.imis_patient_category_flags["child"]
        extension = Extension.construct()
        extension.url = "Age"
        usage_context_system = "http://terminology.hl7.org/CodeSystem/usage-context-type"
        age_type_system = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/usage-context-age-type"
        extension.valueUsageContext = UsageContext.construct()
        extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
        if imis_medication.patient_category & adult_flag:
            coding_adult = cls._build_fhir_coding(code="adult", display="Adult", system=age_type_system)
            cls._append_to_list_codeable_concept(extension, coding_adult)
        if imis_medication.patient_category & child_flag:
            coding_child = cls._build_fhir_coding(code="child", display="Child", system=age_type_system)
            cls._append_to_list_codeable_concept(extension, coding_child)
        extension.valueUsageContext.code = cls._build_fhir_coding(code="age", display="Age",
                                                                  system=usage_context_system)
        return extension

    @classmethod
    def _append_to_list_codeable_concept(cls, extension, coding):
        if type(extension.valueUsageContext.valueCodeableConcept.coding) is not list:
            extension.valueUsageContext.valueCodeableConcept.coding = [coding]
        else:
            extension.valueUsageContext.valueCodeableConcept.coding.append(coding)

    @classmethod
    def build_fhir_care_type(cls, imis_medication):
        if imis_medication.care_type:
            code = cls.build_fhir_act_code(imis_medication)
            display = ItemVenueTypeMapping.item_venue_type[code]
            extension = Extension.construct()
            usage_context_system = "http://terminology.hl7.org/CodeSystem/usage-context-type"
            venue_system = "http://terminology.hl7.org/CodeSystem/v3-ActCode"

            if code != "B":
                extension.url = "CareType"
                extension.valueUsageContext = UsageContext.construct()
                extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
                coding_venue = cls._build_fhir_coding(code=code, display=display, system=venue_system)
                cls._append_to_list_codeable_concept(extension, coding_venue)
            else:
                cls.build_fhir_both_care_type(extension, venue_system)
            extension.valueUsageContext.code = cls._build_fhir_coding(
                code="venue", display="Clinical Venue", system=usage_context_system)
            return extension

    @classmethod
    def build_fhir_both_care_type(cls, extension, venue_system):
        extension.url = "CareType"
        extension.valueUsageContext = UsageContext.construct()
        extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
        coding_venue = cls._build_fhir_coding(code="AMB", display="ambulatory", system=venue_system)
        cls._append_to_list_codeable_concept(extension, coding_venue)
        coding_venue = cls._build_fhir_coding(code="IMP", display="IMP", system=venue_system)
        cls._append_to_list_codeable_concept(extension, coding_venue)

    @classmethod
    def build_fhir_act_code(cls, imis_medication):
        code = ""
        if imis_medication.care_type == "O":
            code = "AMB"
        if imis_medication.care_type == "I":
            code = "IMP"
        if imis_medication.care_type == "B":
            code = "B"
        return code

    @classmethod
    def build_imis_serv_care_type(cls, imis_medication, fhir_medication, errors):
        serv_care_type = fhir_medication.useContext.text
        if not cls.valid_condition(serv_care_type is None,
                                   gettext('Missing activity definition `serv care type` attribute'), errors):
            imis_medication.care_type = serv_care_type

    @classmethod
    def build_imis_unit_price(cls, imis_medication, fhir_extension):
        imis_medication.price = fhir_extension.valueMoney.value

    @classmethod
    def build_imis_medication_type(cls, imis_medication, fhir_extension):
        imis_medication.type = fhir_extension.valueCodeableConcept.coding[0].code

    @classmethod
    def build_imis_medication_frequency(cls, imis_medication, fhir_extension):
        imis_medication.frequency = fhir_extension.valueTiming.repeat.period

    @classmethod
    def build_imis_item_usage_context(cls, imis_medication, fhir_extension):
        extensions = fhir_extension.extension
        for extension in extensions:
            if extension.url in ["Gender", "Age"]:
                usage_context_types = extension.valueUsageContext.valueCodeableConcept.coding
                cls._build_imis_item_patient_category(imis_medication, usage_context_types)
            elif extension.url == "CareType":
                cls._build_imis_item_care_type(imis_medication, extension.valueUsageContext)

    @classmethod
    def _build_imis_item_care_type(cls, imis_medication, usage_context):
        if len(usage_context.valueCodeableConcept.coding) == 2:
            imis_medication.care_type = "B"
        else:
            imis_care_type = ItemVenueTypeMapping.venue_fhir_imis[usage_context.valueCodeableConcept.coding[0].code]
            imis_medication.care_type = imis_care_type

    @classmethod
    def _build_imis_item_patient_category(cls, imis_medication, usage_context_types):
        if not imis_medication.patient_category:
            imis_medication.patient_category = 0
        number = 0
        for usage_context_type in usage_context_types:
            item_pat_cat = usage_context_type.code
            number = number | PatientCategoryMapping.imis_patient_category_flags[item_pat_cat]
        imis_medication.patient_category += number

    @classmethod
    def _build_fhir_coding(cls, code, display, system):
        coding = Coding.construct()
        coding.code = code
        coding.display = _(display)
        if GeneralConfiguration.show_system():
            coding.system = system
        return coding

    @classmethod
    def _validate_fhir_medication_identifier_code(cls, fhir_medication_identifier_code):
        if not fhir_medication_identifier_code:
            raise FHIRException(
                _('Medication FHIR without code - this field is obligatory')
            )

    @classmethod
    def build_fhir_level(cls, fhir_medication: FHIRMedication, imis_medication: Item):
        coding = cls.build_fhir_mapped_coding(ItemContextlevel.item_context_level_coding)
        extension = Extension(
            url=f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/medication-level",
            valueCodeableConcept=CodeableConcept(
                coding=[coding],
                text=coding.display
            )
        )

        if isinstance(fhir_medication.extension, list):
            fhir_medication.extension.append(extension)
        else:
            fhir_medication.extension = [extension]


