from medical.models import Service
from fhir.resources.activitydefinition import ActivityDefinition
from fhir.resources.extension import Extension
from fhir.resources.money import Money
from fhir.resources.usagecontext import UsageContext
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from api_fhir_r4.converters import R4IdentifierConfig, BaseFHIRConverter, ReferenceConverterMixin
from django.utils.translation import gettext

from api_fhir_r4.models.imisModelEnums import ImisCategoryDefinition
from api_fhir_r4.utils import DbManagerUtils, TimeUtils
import core


class ActivityDefinitionConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_activity_definition, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_activity_definition = ActivityDefinition.construct()
        # first to construct is status - obligatory fields
        cls.build_fhir_status(fhir_activity_definition, imis_activity_definition)
        cls.build_fhir_pk(fhir_activity_definition, imis_activity_definition, reference_type)
        cls.build_fhir_identifiers(fhir_activity_definition, imis_activity_definition)
        cls.build_fhir_date(fhir_activity_definition, imis_activity_definition)
        cls.build_fhir_name(fhir_activity_definition, imis_activity_definition)
        cls.build_fhir_title(fhir_activity_definition, imis_activity_definition)
        cls.build_fhir_use_context(fhir_activity_definition, imis_activity_definition)
        cls.build_fhir_topic(fhir_activity_definition, imis_activity_definition)
        cls.build_activity_definition_extension(fhir_activity_definition, imis_activity_definition)
        cls.build_fhir_frequency_extension(fhir_activity_definition, imis_activity_definition)
        return fhir_activity_definition

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_service_code_type()

    @classmethod
    def to_imis_obj(cls, fhir_activity_definition, audit_user_id):
        errors = []
        fhir_activity_definition = ActivityDefinition(**fhir_activity_definition)
        imis_activity_definition = Service()
        cls.build_imis_identifier(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_validity_from(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_code(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_name(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_type(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_pat_cat(imis_activity_definition, fhir_activity_definition)
        cls.build_imis_serv_category(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_care_type(imis_activity_definition, fhir_activity_definition, errors)
        cls.check_errors(errors)
        return imis_activity_definition

    @classmethod
    def get_reference_obj_uuid(cls, imis_activity_definition: Service):
        return imis_activity_definition.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_activity_definition: Service):
        return imis_activity_definition.id

    @classmethod
    def get_reference_obj_code(cls, imis_activity_definition: Service):
        return imis_activity_definition.code

    @classmethod
    def get_fhir_resource_type(cls):
        return ActivityDefinition

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_activity_definition_code = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Service, code=imis_activity_definition_code)

    @classmethod
    def build_fhir_identifiers(cls, fhir_activity_definition, imis_activity_definition):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_activity_definition)
        fhir_activity_definition.identifier = identifiers

    @classmethod
    def build_imis_identifier(cls, imis_activity_definition, fhir_activity_definition, errors):
        value = cls.get_fhir_identifier_by_code(fhir_activity_definition.identifier,
                                                R4IdentifierConfig.get_fhir_uuid_type_code())
        if value:
            imis_activity_definition.code = value
        cls.valid_condition(imis_activity_definition.code is None, gettext('Missing the service code'), errors)

    @classmethod
    def build_fhir_status(cls, fhir_activity_definition, imis_activity_definition):
        fhir_activity_definition.status = "active"

    @classmethod
    def build_fhir_date(cls, fhir_activity_definition, imis_activity_definition):
        fhir_activity_definition.date = imis_activity_definition.validity_from.isoformat()

    @classmethod
    def build_imis_validity_from(cls, imis_activity_definition, fhir_activity_definition, errors):
        validity_from = fhir_activity_definition.date
        if not cls.valid_condition(validity_from is None,
                                   gettext('Missing activity definition `validity from` attribute'), errors):
            imis_activity_definition.validity_from = TimeUtils.str_to_date(validity_from)

    @classmethod
    def build_fhir_name(cls, fhir_activity_definition, imis_activity_definition):
        fhir_activity_definition.name = imis_activity_definition.code

    @classmethod
    def build_imis_serv_code(cls, imis_activity_definition, fhir_activity_definition, errors):
        serv_code = fhir_activity_definition.name
        if not cls.valid_condition(serv_code is None,
                                   gettext('Missing activity definition `serv code` attribute'), errors):
            imis_activity_definition.code = serv_code

    @classmethod
    def build_fhir_title(cls, fhir_activity_definition, imis_activity_definition):
        fhir_activity_definition.title = imis_activity_definition.name

    @classmethod
    def build_imis_serv_name(cls, imis_activity_definition, fhir_activity_definition, errors):
        serv_name = fhir_activity_definition.title
        if not cls.valid_condition(serv_name is None,
                                   gettext('Missing activity definition `serv name` attribute'), errors):
            imis_activity_definition.name = serv_name
   
    @classmethod
    def build_imis_serv_pat_cat(cls, imis_activity_definition, fhir_activity_definition):
        serv_pat_cat = fhir_activity_definition.useContext.code
        number = 0
        if "K" in serv_pat_cat:
            number = number + 8
        if "A" in serv_pat_cat:
            number = number + 4
        if "F" in serv_pat_cat:
            number = number + 2
        if "M" in serv_pat_cat:
            number = number + 1

        imis_activity_definition.patient_category = number

    @classmethod
    def build_imis_serv_category(cls, imis_activity_definition, fhir_activity_definition, errors):
        serv_category = fhir_activity_definition.useContext.text
        if not cls.valid_condition(serv_category is None,
                                   gettext('Missing activity definition `serv category` attribute'), errors):
            imis_activity_definition.category = serv_category

    @classmethod
    def build_imis_serv_care_type(cls, imis_activity_definition, fhir_activity_definition, errors):
        serv_care_type = fhir_activity_definition.useContext.text
        if not cls.valid_condition(serv_care_type is None,
                                   gettext('Missing activity definition `serv care type` attribute'), errors):
            imis_activity_definition.care_type = serv_care_type

    @classmethod
    def build_fhir_topic(cls, fhir_activity_definition, imis_activity_definition):
        fhir_activity_definition.topic = [cls.build_codeable_concept(
            "DefinitionTopic", "http://terminology.hl7.org/CodeSystem/definition-topic",
            text=imis_activity_definition.type)]

    @classmethod
    def build_imis_serv_type(cls, imis_activity_definition, fhir_activity_definition, errors):
        serv_type = fhir_activity_definition.topic
        if not cls.valid_condition(serv_type is None,
                                   gettext('Missing activity definition `serv type` attribute'), errors):
            imis_activity_definition.topic = serv_type

    @classmethod
    def build_fhir_code(cls, fhir_activity_definition, imis_activity_definition):
        fhir_activity_definition.code = cls.build_codeable_concept(imis_activity_definition.code,
                                                                   text=imis_activity_definition.name)

    @classmethod
    def build_activity_definition_extension(cls, fhir_activity_definition, imis_activity_definition):
        cls.build_unit_price(fhir_activity_definition, imis_activity_definition)
        return fhir_activity_definition

    @classmethod
    def build_unit_price(cls, fhir_activity_definition, imis_activity_definition):
        unit_price = cls.build_unit_price_extension(imis_activity_definition.price)
        if type(fhir_activity_definition.extension) is not list:
            fhir_activity_definition.extension = [unit_price]
        else:
            fhir_activity_definition.extension.append(unit_price)

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
    def build_fhir_frequency_extension(cls, fhir_activity_definition, imis_activity_definition):
        serv_price = cls.build_fhir_serv_frequency_extension(imis_activity_definition)
        if type(fhir_activity_definition.extension) is not list:
            fhir_activity_definition.extension = [serv_price]
        else:
            fhir_activity_definition.extension.append(serv_price)

    @classmethod
    def build_fhir_serv_frequency_extension(cls, imis_activity_definition):
        extension = Extension.construct()
        extension.url = "frequency"
        extension.valueInteger = imis_activity_definition.frequency
        return extension

    @classmethod
    def build_fhir_use_context(cls, fhir_activity_definition, imis_activity_definition):
        use_context = cls.build_fhir_use_context_context(imis_activity_definition)
        fhir_activity_definition.useContext = use_context

    @classmethod
    def build_fhir_use_context_context(cls, imis_activity_definition):
        usage_context_gender = \
            cls.__build_usage_context('useContextGender', cls.build_fhir_gender(imis_activity_definition))
        usage_context_age = \
            cls.__build_usage_context('useContextAge', cls.build_fhir_age(imis_activity_definition))
        usage_context_workflow = \
            cls.__build_usage_context('useContextWorkflow',  cls.build_fhir_workflow(imis_activity_definition))
        usage_context_venue = \
            cls.__build_usage_context('useContextVenue', cls.build_fhir_venue(imis_activity_definition))
        usage_context_level = \
            cls.__build_usage_context('useContextLevel', cls.build_fhir_level(imis_activity_definition))

        usage = [usage_context_gender, usage_context_age]
        if usage_context_workflow.valueCodeableConcept.coding[0].display:
            usage.append(usage_context_workflow)
        elif usage_context_venue.valueCodeableConcept.coding[0].display:
            usage.append(usage_context_venue)

        usage.append(usage_context_level)

        for x in usage:
            a = all([a.code for a in x.valueCodeableConcept.coding])
            if a:
                print(x)
        return usage

    @classmethod
    def __build_usage_context(cls, code, codeable_concept):
        usage_context = UsageContext.construct()
        usage_context.valueCodeableConcept = CodeableConcept.construct()
        usage_context.code = Coding.construct()
        usage_context.code.code = code
        usage_context.valueCodeableConcept = codeable_concept
        return usage_context

    @classmethod
    def build_fhir_gender(cls, imis_activity_definition):
        male = cls.build_fhir_male(imis_activity_definition)
        female = cls.build_fhir_female(imis_activity_definition)

        codeable_concept = CodeableConcept.construct()

        if male:
            coding_male = Coding.construct()
            coding_male.code = male
            coding_male.display = "Male"
            if type(codeable_concept.coding) is not list:
                codeable_concept.coding = [coding_male]
            else:
                codeable_concept.coding.append(coding_male)

        if female:
            coding_female = Coding.construct()
            coding_female.code = female
            coding_female.display = "Female"
            if type(codeable_concept.coding) is not list:
                codeable_concept.coding = [coding_female]
            else:
                codeable_concept.coding.append(coding_female)
            codeable_concept.text = "Male or Female"

        return codeable_concept

    @classmethod
    def build_fhir_age(cls, imis_activity_definition):
        adult = cls.build_fhir_adult(imis_activity_definition)
        kid = cls.build_fhir_kid(imis_activity_definition)
        codeable_concept = CodeableConcept.construct()

        if adult:
            coding_adult = Coding.construct()
            coding_adult.code = adult
            coding_adult.display = "Adult"
            if type(codeable_concept.coding) is not list:
                codeable_concept.coding = [coding_adult]
            else:
                codeable_concept.coding.append(coding_adult)
            codeable_concept.text = "Adult"

        if kid:
            coding_kid = Coding.construct()
            coding_kid.code = kid
            coding_kid.display = "Kid"
            if type(codeable_concept.coding) is not list:
                codeable_concept.coding = [coding_kid]
            else:
                codeable_concept.coding.append(coding_kid)
            codeable_concept.text = "Adult or Kid"

        return codeable_concept

    @classmethod
    def build_fhir_venue(cls, imis_activity_definition):
        display = ""
        if imis_activity_definition.care_type == "O":
            display = "Out-patient"
        if imis_activity_definition.care_type == "I":
            display = "In-patient"
        if imis_activity_definition.care_type == "B":
            display = "Both"

        codeable_concept = CodeableConcept.construct()
        coding_venue = Coding.construct()
        coding_venue.code = imis_activity_definition.care_type
        coding_venue.display = display
        if type(codeable_concept.coding) is not list:
            codeable_concept.coding = [coding_venue]
        else:
            codeable_concept.coding.append(coding_venue)
        codeable_concept.text = "Clinical Venue"
        return codeable_concept

    @classmethod
    def build_fhir_level(self, imis_activity_definition: Service):
        # Values for this extension are fixed for medication
        display = ""
        if imis_activity_definition.level == 'S':
            display = 'Simple Service'
        elif imis_activity_definition.level == 'V':
            display = 'Visit'
        elif imis_activity_definition.level == 'D':
            display = 'Day of stay'
        elif imis_activity_definition.level == 'H':
            display = 'Hospital case'

        codeable_concept = CodeableConcept.construct()
        coding_level = Coding.construct()
        coding_level.code = imis_activity_definition.level
        coding_level.display = display
        if type(codeable_concept.coding) is not list:
            codeable_concept.coding = [coding_level]
        else:
            codeable_concept.coding.append(coding_level)
        codeable_concept.text = "Service Level"

        return codeable_concept

    @classmethod
    def build_fhir_workflow(cls, imis_activity_definition):
        codeable_concept = CodeableConcept.construct()
        coding_workflow = Coding.construct()

        if imis_activity_definition.category and imis_activity_definition.category != ' ':
            coding_workflow.code = imis_activity_definition.category
            coding_workflow.display = ImisCategoryDefinition.get_category_display(imis_activity_definition.category)

        if type(codeable_concept.coding) is not list:
            codeable_concept.coding = [coding_workflow]
        else:
            codeable_concept.coding.append(coding_workflow)
        codeable_concept.text = "Workflow Setting"
        return codeable_concept

    @classmethod
    def build_fhir_male(cls, imis_activity_definition):
        item_pat_cat = imis_activity_definition.patient_category
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
    def build_fhir_female(cls, imis_activity_definition):
        item_pat_cat = imis_activity_definition.patient_category
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
    def build_fhir_adult(cls, imis_activity_definition):
        item_pat_cat = imis_activity_definition.patient_category
        adult = ""
        if item_pat_cat > 8:
            kid = "K"
            item_pat_cat = item_pat_cat - 8
        if item_pat_cat >= 4:
            adult = "A"
        return adult

    @classmethod
    def build_fhir_kid(cls, imis_activity_definition):
        item_pat_cat = imis_activity_definition.patient_category
        kid = ""
        if item_pat_cat >= 8:
            kid = "K"
        return kid
