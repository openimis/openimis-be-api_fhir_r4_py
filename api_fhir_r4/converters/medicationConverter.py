from medical.models import Item
from api_fhir_r4.converters import R4IdentifierConfig, BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.models import UsageContextV2 as UsageContext
from fhir.resources.medication import Medication as FHIRMedication
from fhir.resources.extension import Extension
from fhir.resources.money import Money
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from django.utils.translation import gettext
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
        #cls.build_fhir_package_amount(fhir_medication, imis_medication)
        cls.build_medication_extension(fhir_medication, imis_medication)
        cls.build_fhir_code(fhir_medication, imis_medication)
        cls.build_fhir_frequency_extension(fhir_medication, imis_medication)
        cls.build_fhir_topic_extension(fhir_medication, imis_medication)
        cls.build_fhir_use_context(fhir_medication, imis_medication)
        return fhir_medication

    @classmethod
    def to_imis_obj(cls, fhir_medication, audit_user_id):
        errors = []
        fhir_medication = FHIRMedication(**fhir_medication)
        imis_medication = Item()
        cls.build_imis_identifier(imis_medication, fhir_medication, errors)
        cls.build_imis_item_code(imis_medication, fhir_medication, errors)
        cls.build_imis_item_name(imis_medication, fhir_medication, errors)
        cls.build_imis_item_package(imis_medication, fhir_medication, errors)
        cls.check_errors(errors)
        return imis_medication

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_item_code_type()

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
        return DbManagerUtils.get_object_or_none(Item, code=imis_medication_code)

    @classmethod
    def build_fhir_identifiers(cls, fhir_medication, imis_medication):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_medication)
        fhir_medication.identifier = identifiers

    @classmethod
    def build_imis_identifier(cls, imis_medication, fhir_medication, errors):
        value = cls.get_fhir_identifier_by_code(fhir_medication.identifier, R4IdentifierConfig.get_fhir_uuid_type_code())
        if value:
            imis_medication.code = value
        cls.valid_condition(imis_medication.code is None, gettext('Missing the item code'), errors)

    @classmethod
    def build_fhir_package_form(cls, fhir_medication, imis_medication):
        #form = cls.split_package_form(imis_medication.package)
        #fhir_medication.form = form
        fhir_medication.form = cls.build_codeable_concept("package", text=imis_medication.package.lstrip())

    """
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
        amount = cls.split_package_amount(imis_medication.package)
        fhir_medication.amount = amount

    @classmethod
    def split_package_amount(cls, amount):
        amount = amount.lstrip()
        if " " not in amount:
            return None
        if " " in amount:
            amount = amount.split(' ', 1)
            amount = amount[0]
            return int(amount)
    """

    @classmethod
    def build_medication_extension(cls, fhir_medication, imis_medication):
        cls.build_unit_price(fhir_medication, imis_medication)
        return fhir_medication

    @classmethod
    def build_unit_price(cls, fhir_medication, imis_medication):
        unit_price = cls.build_unit_price_extension(imis_medication.price)
        if type(fhir_medication.extension) is not list:
           fhir_medication.extension = [unit_price]
        else:
           fhir_medication.extension.append(unit_price)

    @classmethod
    def build_unit_price_extension(cls, value):
        extension = Extension.construct()
        money = Money.construct()
        extension.url = "unitPrice"
        extension.valueMoney = money
        extension.valueMoney.value = value
        if hasattr(core, 'currency'):
            extension.valueMoney.currency = core.currency
        return extension

    @classmethod
    def build_fhir_code(cls, fhir_medication, imis_medication):
        fhir_medication.code = cls.build_codeable_concept(imis_medication.code, text=imis_medication.name)

    @classmethod
    def build_imis_item_code(cls, imis_medication, fhir_medication, errors):
        item_code = fhir_medication.code.coding
        if not cls.valid_condition(item_code is None,
                                   gettext('Missing medication `item_code` attribute'), errors):
            # get the code of item
            if type(item_code) is not list:
                imis_medication.code = item_code.code
            else:
                item_code_element = item_code[0]
                imis_medication.code = item_code_element.code

    @classmethod
    def build_imis_item_name(cls, imis_medication, fhir_medication, errors):
        item_name = fhir_medication.code.text
        if not cls.valid_condition(item_name is None,
                                   gettext('Missing medication `item_name` attribute'), errors):
            imis_medication.name = item_name

    @classmethod
    def build_imis_item_package(cls, imis_medication, fhir_medication, errors):
        form = fhir_medication.form
        amount = fhir_medication.amount
        package = [amount, form]
        if not cls.valid_condition(package is None,
                                   gettext('Missing medication `form` and `amount` attribute'), errors):
            imis_medication.package = package

    @classmethod
    def build_fhir_frequency_extension(cls, fhir_medication, imis_medication):
        serv_price = cls.build_fhir_item_frequency_extension(imis_medication)
        if type(fhir_medication.extension) is not list:
            fhir_medication.extension = [serv_price]
        else:
            fhir_medication.extension.append(serv_price)

    @classmethod
    def build_fhir_item_frequency_extension(cls, imis_medication):
        extension = Extension.construct()
        extension.url = "frequency"
        extension.valueInteger = imis_medication.frequency
        return extension

    @classmethod
    def build_fhir_topic_extension(cls, fhir_medication, imis_medication):
        item_type = cls.build_fhir_item_type_extension(imis_medication)
        if type(fhir_medication.extension) is not list:
            fhir_medication.extension = [item_type]
        else:
            fhir_medication.extension.append(item_type)

    @classmethod
    def build_fhir_item_type_extension(cls, imis_medication):
        extension = Extension.construct()
        extension.url = "topic"
        extension.valueCodeableConcept = cls.build_codeable_concept("DefinitionTopic",
                                                                    "http://terminology.hl7.org/CodeSystem/definition-topic",
                                                                    text=imis_medication.type)
        return extension

    @classmethod
    def build_fhir_use_context(cls, fhir_medication, imis_medication):
        gender = cls.build_fhir_gender(imis_medication)
        # check only the first to be sure if we have list, the
        # next ones for sure will be a part of list of extensions
        if type(fhir_medication.extension) is not list:
            fhir_medication.extension = [gender]
        else:
            fhir_medication.extension.append(gender)
        age = cls.build_fhir_age(imis_medication)
        fhir_medication.extension.append(age)
        venue = cls.build_fhir_venue(imis_medication)
        fhir_medication.extension.append(venue)
        level = cls.build_fhir_level(imis_medication)
        fhir_medication.extension.append(level)

    @classmethod
    def build_fhir_gender(cls, imis_medication):
        male = cls.build_fhir_male(imis_medication)
        female = cls.build_fhir_female(imis_medication)
        if male == "":
            male = None
        if female == "":
            female = None
        extension = Extension.construct()
        extension.url = "useContextGender"
        extension.valueUsageContext = UsageContext.construct()
        extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
        if male is not None:
            coding_male = Coding.construct()
            coding_male.code = male
            coding_male.display = "Male"
            if type(extension.valueUsageContext.valueCodeableConcept.coding) is not list:
                extension.valueUsageContext.valueCodeableConcept.coding = [coding_male]
            else:
                extension.valueUsageContext.valueCodeableConcept.coding.append(coding_male)
        if female is not None:
            coding_female = Coding.construct()
            coding_female.code = female
            coding_female.display = "Female"
            if type(extension.valueUsageContext.valueCodeableConcept.coding) is not list:
                extension.valueUsageContext.valueCodeableConcept.coding = [coding_female]
            else:
                extension.valueUsageContext.valueCodeableConcept.coding.append(coding_female)
            extension.valueUsageContext.valueCodeableConcept.text = "Male or Female"
        extension.valueUsageContext.code = Coding.construct()
        extension.valueUsageContext.code.code = "gender"
        return extension

    @classmethod
    def build_fhir_age(cls, imis_medication):
        adult = cls.build_fhir_adult(imis_medication)
        kid = cls.build_fhir_kid(imis_medication)
        if adult == "":
            adult = None
        if kid == "":
            kid = None
        extension = Extension.construct()
        extension.url = "useContextAge"
        extension.valueUsageContext = UsageContext.construct()
        extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
        if adult is not None:
            coding_adult = Coding.construct()
            coding_adult.code = adult
            coding_adult.display = "Adult"
            if type(extension.valueUsageContext.valueCodeableConcept.coding) is not list:
                extension.valueUsageContext.valueCodeableConcept.coding = [coding_adult]
            else:
                extension.valueUsageContext.valueCodeableConcept.coding.append(coding_adult)
        if kid is not None:
            coding_kid = Coding.construct()
            coding_kid.code = kid
            coding_kid.display = "Kid"
            if type(extension.valueUsageContext.valueCodeableConcept.coding) is not list:
                extension.valueUsageContext.valueCodeableConcept.coding = [coding_kid]
            else:
                extension.valueUsageContext.valueCodeableConcept.coding.append(coding_kid)
            extension.valueUsageContext.valueCodeableConcept.text = "Adult or Kid"
        extension.valueUsageContext.code = Coding.construct()
        extension.valueUsageContext.code.code = "age"
        return extension

    @classmethod
    def build_fhir_venue(cls, imis_medication):
        display = ""
        if imis_medication.care_type == "O":
            display = "Out-patient"
        if imis_medication.care_type == "I":
            display = "In-patient"
        if imis_medication.care_type == "B":
            display = "Both"

        extension = Extension.construct()
        if imis_medication.care_type is not None:
            extension.url = "useContextVenue"
            extension.valueUsageContext = UsageContext.construct()
            extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
            coding_venue = Coding.construct()
            coding_venue.code = imis_medication.care_type
            coding_venue.display = display
            if type(extension.valueUsageContext.valueCodeableConcept.coding) is not list:
                extension.valueUsageContext.valueCodeableConcept.coding = [coding_venue]
            else:
                extension.valueUsageContext.valueCodeableConcept.coding.append(coding_venue)
            extension.valueUsageContext.valueCodeableConcept.text = "Clinical Venue"
            extension.valueUsageContext.code = Coding.construct()
            extension.valueUsageContext.code.code = "venue"
        return extension

    @classmethod
    def build_fhir_level(self, imis_medication):
        # Values for this extension are fixed for medication
        extension = Extension.construct()
        extension.url = 'useContextLevel'
        extension.valueUsageContext = UsageContext.construct()
        extension.valueUsageContext.valueCodeableConcept = CodeableConcept.construct()
        coding = Coding.construct()
        coding.code = 'M'
        coding.display = 'Medication'
        if type(extension.valueUsageContext.valueCodeableConcept.coding) is not list:
            extension.valueUsageContext.valueCodeableConcept.coding = [coding]
        else:
            extension.valueUsageContext.valueCodeableConcept.coding.append(coding)
        extension.valueUsageContext.valueCodeableConcept.text = "Item Level"
        extension.valueUsageContext.code = Coding.construct()
        extension.valueUsageContext.code.code = 'level'
        return extension

    @classmethod
    def build_fhir_male(cls, imis_medication):
        item_pat_cat = imis_medication.patient_category
        male = ""
        if item_pat_cat > 8:
            kid = "K"
            item_pat_cat = item_pat_cat - 8
        if item_pat_cat > 4:
            adult = "A"
            item_pat_cat = item_pat_cat - 4
        if item_pat_cat > 2:
            female = "F"
            item_pat_cat = item_pat_cat - 2
        if item_pat_cat == 1:
            male = "M"
        return male

    @classmethod
    def build_fhir_female(cls, imis_medication):
        item_pat_cat = imis_medication.patient_category
        female = ""
        if item_pat_cat > 8:
            kid = "K"
            item_pat_cat = item_pat_cat - 8
        if item_pat_cat > 4:
            adult = "A"
            item_pat_cat = item_pat_cat - 4
        if item_pat_cat >= 2:
            female = "F"
        return female

    @classmethod
    def build_fhir_adult(cls, imis_medication):
        item_pat_cat = imis_medication.patient_category
        adult = ""
        if item_pat_cat > 8:
            kid = "K"
            item_pat_cat = item_pat_cat - 8
        if item_pat_cat >= 4:
            adult = "A"
        return adult

    @classmethod
    def build_fhir_kid(cls, imis_medication):
        item_pat_cat = imis_medication.patient_category
        kid = ""
        if item_pat_cat >= 8:
            kid = "K"
        return kid

    @classmethod
    def build_imis_item_pat_cat(cls, imis_medication, fhir_medication):
        item_pat_cat = fhir_medication.useContext.code
        number = 0
        if "K" in item_pat_cat:
            number = number + 8
        if "A" in item_pat_cat:
            number = number + 4
        if "F" in item_pat_cat:
            number = number + 2
        if "M" in item_pat_cat:
            number = number + 1

        imis_medication.patient_category = number

    @classmethod
    def build_imis_serv_care_type(cls, imis_medication, fhir_medication, errors):
        serv_care_type = fhir_medication.useContext.text
        if not cls.valid_condition(serv_care_type is None,
                                   gettext('Missing activity definition `serv care type` attribute'), errors):
            imis_medication.care_type = serv_care_type

