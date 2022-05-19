from fhir.resources.timing import Timing, TimingRepeat
from medical.models import Service
from fhir.resources.activitydefinition import ActivityDefinition
from fhir.resources.extension import Extension
from fhir.resources.money import Money
from fhir.resources.usagecontext import UsageContext
from fhir.resources.codeableconcept import CodeableConcept

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.converters import R4IdentifierConfig, BaseFHIRConverter, ReferenceConverterMixin
from django.utils.translation import gettext

from api_fhir_r4.mapping.activityDefinitionMapping import ServiceTypeMapping, UseContextMapping, VenueMapping, \
    WorkflowMapping, ServiceLevelMapping
from api_fhir_r4.mapping.patientMapping import PatientCategoryMapping
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
        cls.build_fhir_timing(fhir_activity_definition, imis_activity_definition)
        cls.build_fhir_activity_definition_extension(fhir_activity_definition, imis_activity_definition)
        cls.build_fhir_level(fhir_activity_definition, imis_activity_definition)
        return fhir_activity_definition

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

    @classmethod
    def to_imis_obj(cls, fhir_activity_definition, audit_user_id):
        errors = []
        fhir_activity_definition = ActivityDefinition(**fhir_activity_definition)
        imis_activity_definition = Service()
        imis_activity_definition.audit_user_id = audit_user_id
        cls.build_imis_identifier(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_validity_from(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_price(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_frequency(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_code(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_name(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_type(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_pat_cat(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_category(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_serv_care_type(imis_activity_definition, fhir_activity_definition, errors)
        cls.build_imis_level(imis_activity_definition, fhir_activity_definition, errors)
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
        return DbManagerUtils.get_object_or_none(Service, uuid=imis_activity_definition_code)

    @classmethod
    def build_fhir_identifiers(cls, fhir_activity_definition, imis_activity_definition):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_activity_definition)
        fhir_activity_definition.identifier = identifiers

    @classmethod
    def build_imis_price(cls, imis_activity_definition, fhir_activity_definition, errors):
        extension_base_url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/unit-price"
        extension = cls.get_fhir_extension_by_url(fhir_activity_definition.extension,
                                                  extension_base_url)

        if extension and hasattr(extension, "valueMoney"):
            imis_activity_definition.price = extension.valueMoney.value

    @classmethod
    def build_imis_frequency(cls, imis_activity_definition, fhir_activity_definition, errors):
        value = None
        try:
            if hasattr(fhir_activity_definition, "timingTiming"):
                value = fhir_activity_definition.timingTiming.repeat.period
        except AttributeError:
            errors.append(gettext('Invalid activity definition `timingTiming` attribute'))
        finally:
            imis_activity_definition.frequency = value

    @classmethod
    def build_imis_identifier(cls, imis_activity_definition, fhir_activity_definition, errors):
        value = cls.get_fhir_identifier_by_code(fhir_activity_definition.identifier,
                                                R4IdentifierConfig.get_fhir_uuid_type_code())
        if value:
            imis_activity_definition.uuid = value

        value = cls.get_fhir_identifier_by_code(fhir_activity_definition.identifier,
                                                ActivityDefinitionConverter.get_fhir_code_identifier_type())
        if value:
            imis_activity_definition.code = value

        cls.valid_condition(not imis_activity_definition.code,
                            gettext('Missing the service code'), errors)

    @classmethod
    def build_fhir_status(cls, fhir_activity_definition, imis_activity_definition):
        fhir_activity_definition.status = "active"

    @classmethod
    def build_fhir_date(cls, fhir_activity_definition, imis_activity_definition):
        fhir_activity_definition.date = imis_activity_definition.validity_from.isoformat()

    @classmethod
    def build_imis_validity_from(cls, imis_activity_definition, fhir_activity_definition, errors):
        validity_from = fhir_activity_definition.date
        if not cls.valid_condition(not validity_from,
                                   gettext('Missing activity definition `validity from` attribute'), errors):
            imis_activity_definition.validity_from = TimeUtils.str_iso_to_date(validity_from)

    @classmethod
    def build_fhir_name(cls, fhir_activity_definition, imis_activity_definition):
        fhir_activity_definition.name = imis_activity_definition.code

    @classmethod
    def build_imis_serv_code(cls, imis_activity_definition, fhir_activity_definition, errors):
        serv_code = fhir_activity_definition.name
        if not cls.valid_condition(not serv_code,
                                   gettext('Missing activity definition `serv code` attribute'), errors):
            imis_activity_definition.code = serv_code

    @classmethod
    def build_fhir_title(cls, fhir_activity_definition, imis_activity_definition):
        fhir_activity_definition.title = imis_activity_definition.name

    @classmethod
    def build_imis_serv_name(cls, imis_activity_definition, fhir_activity_definition, errors):
        serv_name = fhir_activity_definition.title
        if not cls.valid_condition(not serv_name,
                                   gettext('Missing activity definition `serv name` attribute'), errors):
            imis_activity_definition.name = serv_name

    @classmethod
    def build_imis_serv_pat_cat(cls, imis_activity_definition, fhir_activity_definition, errors):
        use_context_codes = ["gender", "age"]
        pat_cat_flag = 0
        try:
            for use_context_code in use_context_codes:
                use_context = cls.get_use_context_by_code(fhir_activity_definition.useContext, use_context_code)
                if use_context and len(use_context.valueCodeableConcept.coding) > 0:
                    for coding in use_context.valueCodeableConcept.coding:
                        pat_cat_flag = pat_cat_flag | PatientCategoryMapping.imis_patient_category_flags[coding.code]
        except AttributeError or TypeError or KeyError:
            errors.append(gettext('Invalid activity definition `use context - age/gender` attribute'))
        finally:
            imis_activity_definition.patient_category = pat_cat_flag

    @classmethod
    def build_imis_serv_category(cls, imis_activity_definition, fhir_activity_definition, errors):
        use_context = cls.get_use_context_by_code(fhir_activity_definition.useContext, "workflow")
        service_category = None
        try:
            if use_context and len(use_context.valueCodeableConcept.coding) > 0:
                service_category = use_context.valueCodeableConcept.coding[0].code
        except AttributeError or TypeError or KeyError:
            errors.append(gettext('Invalid activity definition `use context - workflow` attribute'))
        finally:
            imis_activity_definition.category = service_category

    @classmethod
    def build_imis_serv_care_type(cls, imis_activity_definition, fhir_activity_definition, errors):
        use_context = cls.get_use_context_by_code(fhir_activity_definition.useContext, "venue")
        care_type = None
        try:
            if not use_context or len(use_context.valueCodeableConcept.coding) == 0:
                errors.append(gettext('Missing activity definition `use context - venue` attribute'))
            else:
                for coding in use_context.valueCodeableConcept.coding:
                    if coding.code not in VenueMapping.imis_venue_coding.keys():
                        raise AttributeError
                    if not care_type:
                        care_type = VenueMapping.imis_venue_coding[coding.code]
                    elif care_type != coding.code:
                        care_type = Service.CARE_TYPE_BOTH
        except AttributeError or TypeError or KeyError:
            errors.append(gettext('Invalid activity definition `use context - venue` attribute'))
        finally:
            imis_activity_definition.care_type = care_type

    @classmethod
    def build_imis_serv_type(cls, imis_activity_definition, fhir_activity_definition, errors):
        service_type = None
        try:
            if hasattr(fhir_activity_definition, "topic"):
                service_type = cls.get_first_coding_from_codeable_concept(fhir_activity_definition.topic[0]).code
                if service_type not in ServiceTypeMapping.fhir_service_type_coding.keys():
                    raise AttributeError
        except AttributeError:
            errors.append(gettext('Invalid activity definition `topic` attribute'))
        finally:
            imis_activity_definition.type = service_type

    @classmethod
    def build_fhir_activity_definition_extension(cls, fhir_activity_definition, imis_activity_definition):
        cls.build_fhir_unit_price(fhir_activity_definition, imis_activity_definition)
        return fhir_activity_definition

    @classmethod
    def build_fhir_unit_price(cls, fhir_activity_definition, imis_activity_definition):
        unit_price = cls.build_fhir_unit_price_extension(imis_activity_definition.price)
        if type(fhir_activity_definition.extension) is not list:
            fhir_activity_definition.extension = [unit_price]
        else:
            fhir_activity_definition.extension.append(unit_price)

    @classmethod
    def build_fhir_unit_price_extension(cls, value):
        extension = Extension.construct()
        money = Money.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/unit-price"
        extension.valueMoney = money
        extension.valueMoney.value = value
        if hasattr(core, 'currency'):
            extension.valueMoney.currency = core.currency
        return extension

    @classmethod
    def build_fhir_topic(cls, fhir_activity_definition, imis_activity_definition):
        topic = [cls.build_codeable_concept_from_coding(cls.build_fhir_topic_coding(imis_activity_definition.type))]
        fhir_activity_definition.topic = topic

    @classmethod
    def build_fhir_use_context(cls, fhir_activity_definition, imis_activity_definition):
        usage = []
        if imis_activity_definition.patient_category:
            usage.append(cls.build_fhir_gender_usage_context(imis_activity_definition))
            usage.append(cls.build_fhir_age_usage_context(imis_activity_definition))

        if imis_activity_definition.category and not imis_activity_definition.category.isspace():
            usage.append(cls.build_fhir_workflow_usage_context(imis_activity_definition))

        usage.append(cls.build_fhir_venue_usage_context(imis_activity_definition))

        usage = [usage_item for usage_item in usage if len(usage_item.valueCodeableConcept.coding) > 0]
        fhir_activity_definition.useContext = usage

    @classmethod
    def build_fhir_usage_context(cls, code, codeable_concept):
        usage_context = UsageContext.construct()
        usage_context.valueCodeableConcept = codeable_concept
        usage_context.code = code
        return usage_context

    @classmethod
    def build_fhir_gender_usage_context(cls, imis_activity_definition):
        return cls.build_fhir_usage_context(cls.build_fhir_usage_context_coding("gender"),
                                            cls.build_fhir_gender(imis_activity_definition))

    @classmethod
    def build_fhir_age_usage_context(cls, imis_activity_definition):
        return cls.build_fhir_usage_context(cls.build_fhir_usage_context_coding("age"),
                                            cls.build_fhir_age(imis_activity_definition))

    @classmethod
    def build_fhir_venue_usage_context(cls, imis_activity_definition):
        return cls.build_fhir_usage_context(cls.build_fhir_usage_context_coding("venue"),
                                            cls.build_fhir_venue(imis_activity_definition))

    @classmethod
    def build_fhir_workflow_usage_context(cls, imis_activity_definition):
        return cls.build_fhir_usage_context(cls.build_fhir_usage_context_coding("workflow"),
                                            cls.build_fhir_workflow(imis_activity_definition))

    @classmethod
    def build_fhir_workflow(cls, imis_activity_definition):
        codeable_concept = CodeableConcept.construct()
        codeable_concept.coding = []

        codeable_concept.coding.append(cls.build_fhir_workflow_coding(imis_activity_definition.category))
        codeable_concept.text = codeable_concept.coding[0].display

        return codeable_concept

    @classmethod
    def build_fhir_venue(cls, imis_activity_definition):
        codeable_concept = CodeableConcept.construct()
        codeable_concept.coding = []

        ambulatory_venue = imis_activity_definition.care_type in [Service.CARE_TYPE_OUT_PATIENT, Service.CARE_TYPE_BOTH]
        if ambulatory_venue:
            ambulatory_coding = cls.build_fhir_venue_coding(Service.CARE_TYPE_OUT_PATIENT)
            codeable_concept.coding.append(ambulatory_coding)

        imp_venue = imis_activity_definition.care_type in [Service.CARE_TYPE_IN_PATIENT, Service.CARE_TYPE_BOTH]
        if imp_venue:
            imp_coding = cls.build_fhir_venue_coding(Service.CARE_TYPE_IN_PATIENT)
            codeable_concept.coding.append(imp_coding)

        codeable_concept.text = " or ".join([coding.display for coding in codeable_concept.coding])

        return codeable_concept

    @classmethod
    def build_fhir_gender(cls, imis_activity_definition):
        codeable_concept = CodeableConcept.construct()
        codeable_concept.coding = []

        male_flag = PatientCategoryMapping.imis_patient_category_flags["male"]
        if imis_activity_definition.patient_category & male_flag:
            male_coding = cls.build_fhir_patient_category_coding("male")
            codeable_concept.coding.append(male_coding)

        female_flag = PatientCategoryMapping.imis_patient_category_flags["female"]
        if imis_activity_definition.patient_category & female_flag:
            female_coding = cls.build_fhir_patient_category_coding("female")
            codeable_concept.coding.append(female_coding)

        codeable_concept.text = " or ".join([coding.display for coding in codeable_concept.coding])

        return codeable_concept

    @classmethod
    def build_fhir_age(cls, imis_activity_definition):
        codeable_concept = CodeableConcept.construct()
        codeable_concept.coding = []

        adult_flag = PatientCategoryMapping.imis_patient_category_flags["adult"]
        if imis_activity_definition.patient_category & adult_flag:
            adult_coding = cls.build_fhir_patient_category_coding("adult")
            codeable_concept.coding.append(adult_coding)

        child_flag = PatientCategoryMapping.imis_patient_category_flags["child"]
        if imis_activity_definition.patient_category & child_flag:
            child_coding = cls.build_fhir_patient_category_coding("child")
            codeable_concept.coding.append(child_coding)

        codeable_concept.text = " or ".join([coding.display for coding in codeable_concept.coding])

        return codeable_concept

    @classmethod
    def build_fhir_usage_context_coding(cls, usage_context):
        return cls.build_fhir_mapped_coding(UseContextMapping.fhir_use_context_coding[usage_context])

    @classmethod
    def build_fhir_patient_category_coding(cls, category):
        return cls.build_fhir_mapped_coding(PatientCategoryMapping.fhir_patient_category_coding[category])

    @classmethod
    def build_fhir_venue_coding(cls, venue):
        return cls.build_fhir_mapped_coding(VenueMapping.fhir_venue_coding[venue])

    @classmethod
    def build_fhir_workflow_coding(cls, workflow):
        return cls.build_fhir_mapped_coding(WorkflowMapping.fhir_workflow_coding[workflow])

    @classmethod
    def build_fhir_topic_coding(cls, topic):
        return cls.build_fhir_mapped_coding(ServiceTypeMapping.fhir_service_type_coding[topic])

    @classmethod
    def build_fhir_timing(cls, fhir_activity_definition, imis_activity_definition):
        timing = Timing.construct()
        timing_repeat = TimingRepeat.construct()

        timing_repeat.frequency = 1
        timing_repeat.period = imis_activity_definition.frequency
        timing_repeat.periodUnit = "d"

        timing.repeat = timing_repeat
        fhir_activity_definition.timingTiming = timing

    @classmethod
    def build_fhir_level(cls, fhir_activity_definition: ActivityDefinition, imis_activity_definition: Service):
        imis_level = imis_activity_definition.level
        coding_data = ServiceLevelMapping.fhir_service_level_coding.get(imis_level, None)
        if coding_data:
            coding = cls.build_fhir_mapped_coding(coding_data)
            extension = Extension(
                url=f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/activity-definition-level",
                valueCodeableConcept=CodeableConcept(
                    coding=[coding],
                    text=coding.display
                )
            )
            if isinstance(fhir_activity_definition.extension, list):
                fhir_activity_definition.extension.append(extension)
            else:
                fhir_activity_definition.extension = [extension]

    @classmethod
    def build_imis_level(cls, imis_service: Service, fhir_service: ActivityDefinition, errors: list):
        level_ext = next(
            (ext for ext in fhir_service.extension if ext.url.lower().endswith('activity-definition-level')),
            None
        )

        if level_ext:
            code = level_ext.valueCodeableConcept.coding[0].code
            valid_codes = ServiceLevelMapping.fhir_service_level_coding.keys()

            if code not in valid_codes:
                errors.append(
                    F"Invalid code system {code} for ActivityDefinition Level, "
                    F"Valid codes are: {valid_codes}"
                )

            imis_service.level = code
