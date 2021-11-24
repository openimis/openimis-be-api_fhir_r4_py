import base64
import hashlib
import re

from claim import ClaimItemSubmit, ClaimServiceSubmit, ClaimConfig
from claim.models import Claim, ClaimItem, ClaimService, ClaimAttachment
from location.models import HealthFacility
from medical.models import Diagnosis, Item, Service
from django.utils.translation import gettext
import core

from api_fhir_r4.configurations import R4IdentifierConfig, R4ClaimConfig
from api_fhir_r4.converters import BaseFHIRConverter, LocationConverter, PatientConverter, PractitionerConverter, \
    ReferenceConverterMixin, PractitionerRoleConverter
from api_fhir_r4.converters.conditionConverter import ConditionConverter
from api_fhir_r4.converters.medicationConverter import MedicationConverter
from api_fhir_r4.converters.healthcareServiceConverter import HealthcareServiceConverter
from api_fhir_r4.converters.activityDefinitionConverter import ActivityDefinitionConverter
from api_fhir_r4.converters.coverageConverter import CoverageConverter
from api_fhir_r4.models import ClaimV2 as FHIRClaim, ClaimInsuranceV2 as ClaimInsurance
from api_fhir_r4.models.imisModelEnums import ImisClaimIcdTypes
from fhir.resources.attachment import Attachment
from fhir.resources.period import Period
from fhir.resources.claim import ClaimDiagnosis, ClaimSupportingInfo, ClaimItem as FHIRClaimItem
from fhir.resources.extension import Extension
from fhir.resources.money import Money
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference

from api_fhir_r4.utils import TimeUtils, FhirUtils, DbManagerUtils
from api_fhir_r4.exceptions import FHIRRequestProcessException


class ClaimConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_claim, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        # there are three required fields - they must be
        # created at the beginning
        fhir_claim = {}
        fhir_claim['created'] = imis_claim.date_claimed.isoformat()
        cls.build_fhir_status(fhir_claim)
        cls.build_fhir_use(fhir_claim)
        fhir_claim = FHIRClaim(**fhir_claim)
        # then build another fields
        cls.build_fhir_pk(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_identifiers(fhir_claim, imis_claim)

        fhir_claim.created = imis_claim.date_claimed.isoformat()
        fhir_claim.facility = cls._build_facility_reference(imis_claim, reference_type)
        fhir_claim.patient = cls._build_patient_reference(imis_claim, reference_type)
        fhir_claim.enterer = cls._build_practitioner_reference(imis_claim, reference_type)

        cls.build_fhir_billable_period(fhir_claim, imis_claim)
        cls.build_fhir_diagnoses(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_total(fhir_claim, imis_claim)
        cls.build_fhir_type(fhir_claim, imis_claim)
        cls.build_fhir_supportingInfo(fhir_claim, imis_claim)
        cls.build_fhir_items(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_provider(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_priority(fhir_claim)
        cls.build_fhir_insurance(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_attachments(fhir_claim, imis_claim)
        return fhir_claim

    @classmethod
    def to_imis_obj(cls, fhir_claim, audit_user_id):
        errors = []
        fhir_claim = FHIRClaim(**fhir_claim)
        imis_claim = Claim()
        cls.build_imis_date_claimed(imis_claim, fhir_claim, errors)
        cls.build_imis_health_facility(errors, fhir_claim, imis_claim)
        cls.build_imis_identifier(imis_claim, fhir_claim, errors)
        cls.build_imis_patient(imis_claim, fhir_claim, errors)
        cls.build_imis_date_range(imis_claim, fhir_claim, errors)
        cls.build_imis_diagnoses(imis_claim, fhir_claim, errors)
        cls.build_imis_total_claimed(imis_claim, fhir_claim, errors)
        cls.build_imis_claim_admin(imis_claim, fhir_claim, errors)
        cls.build_imis_visit_type(imis_claim, fhir_claim)
        cls.build_imis_supportingInfo(imis_claim, fhir_claim)
        cls.build_imis_submit_items_and_services(imis_claim, fhir_claim)
        cls.build_imis_attachments(imis_claim, fhir_claim)
        #cls.build_imis_adjuster(imis_claim, fhir_claim, errors)
        cls.check_errors(errors)
        return imis_claim

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_claim_code_type()

    @classmethod
    def get_reference_obj_id(cls, imis_claim):
        return imis_claim.id

    @classmethod
    def get_reference_obj_uuid(cls, imis_claim):
        return imis_claim.uuid

    @classmethod
    def get_fhir_resource_type(cls):
        return FHIRClaim

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_claim_code = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Claim, code=imis_claim_code)

    @classmethod
    def build_imis_date_claimed(cls, imis_claim, fhir_claim, errors):
        if fhir_claim.created:
            imis_claim.date_claimed = TimeUtils.str_to_date(fhir_claim.created)
        cls.valid_condition(imis_claim.date_claimed is None, gettext('Missing the date of creation'), errors)

    @classmethod
    def build_fhir_identifiers(cls, fhir_claim, imis_claim):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_claim)
        fhir_claim.identifier = identifiers

    @classmethod
    def build_imis_identifier(cls, imis_claim, fhir_claim, errors):
        value = cls.get_fhir_identifier_by_code(fhir_claim.identifier, R4IdentifierConfig.get_fhir_claim_code_type())
        if value:
            imis_claim.code = value
        cls.valid_condition(imis_claim.code is None, gettext('Missing the claim code'), errors)

    @classmethod
    def build_imis_patient(cls, imis_claim, fhir_claim, errors):
        if fhir_claim.patient:
            insuree = PatientConverter.get_imis_obj_by_fhir_reference(fhir_claim.patient)
            if insuree:
                imis_claim.insuree = insuree
                imis_claim.insuree_chf_code = insuree.chf_id
        cls.valid_condition(imis_claim.insuree is None, gettext('Missing the patient reference'), errors)

    @classmethod
    def build_imis_health_facility(cls, errors, fhir_claim, imis_claim):
        if fhir_claim.facility:
            _, hfId = fhir_claim.facility.reference.split("/")
            health_facility = DbManagerUtils.get_object_or_none(HealthFacility, uuid=hfId)
            if health_facility:
                imis_claim.health_facility = health_facility
                imis_claim.health_facility_code = health_facility.code
        cls.valid_condition(imis_claim.health_facility is None, gettext('Missing the facility reference'), errors)

    @classmethod
    def build_fhir_billable_period(cls, fhir_claim, imis_claim):
        billable_period = Period.construct()
        if imis_claim.date_from:
            billable_period.start = imis_claim.date_from.isoformat()
        if imis_claim.date_to:
            billable_period.end = imis_claim.date_to.isoformat()
        fhir_claim.billablePeriod = billable_period

    @classmethod
    def build_imis_date_range(cls, imis_claim, fhir_claim, errors):
        billable_period = fhir_claim.billablePeriod
        if billable_period:
            if billable_period.start:
                imis_claim.date_from = TimeUtils.str_to_date(billable_period.start)
            if billable_period.end:
                imis_claim.date_to = TimeUtils.str_to_date(billable_period.end)
        cls.valid_condition(imis_claim.date_from is None, gettext('Missing the billable start date'), errors)
    """
    @classmethod
    def build_fhir_diagnoses(cls, fhir_claim, imis_claim):
        diagnoses = []
        cls.build_fhir_diagnosis(diagnoses, imis_claim.icd.code, ImisClaimIcdTypes.ICD_0.value)
        if imis_claim.icd_1:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_1, ImisClaimIcdTypes.ICD_1.value)
        if imis_claim.icd_2:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_2, ImisClaimIcdTypes.ICD_2.value)
        if imis_claim.icd_3:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_3, ImisClaimIcdTypes.ICD_3.value)
        if imis_claim.icd_4:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_4, ImisClaimIcdTypes.ICD_4.value)
        fhir_claim.diagnosis = diagnoses
    
    @classmethod
    def build_fhir_diagnosis(cls, diagnoses, icd_code, icd_type):
        claim_diagnosis = ClaimDiagnosis()
        claim_diagnosis.sequence = FhirUtils.get_next_array_sequential_id(diagnoses)
        #claim_diagnosis.diagnosisCodeableConcept = cls.build_codeable_concept(icd_code, None)
        fhir_condition = Condition()
        imis_claim = Claim()

        claim_diagnosis.diagnosisReference = ConditionConverter.build_fhir_resource_reference(imis_claim.code)
        claim_diagnosis.type = [cls.build_simple_codeable_concept(icd_type)]
        diagnoses.append(claim_diagnosis)
    """

    @classmethod
    def build_fhir_diagnoses(cls, fhir_claim, imis_claim, reference_type):
        diagnoses = []
        cls.build_fhir_diagnosis(diagnoses, imis_claim.icd, ImisClaimIcdTypes.ICD_0.value, reference_type)
        if imis_claim.icd_1 is not None:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_1, ImisClaimIcdTypes.ICD_1.value, reference_type)
        if imis_claim.icd_2 is not None:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_2, ImisClaimIcdTypes.ICD_2.value, reference_type)
        if imis_claim.icd_3 is not None:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_3, ImisClaimIcdTypes.ICD_3.value, reference_type)
        if imis_claim.icd_4 is not None:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_4, ImisClaimIcdTypes.ICD_4.value, reference_type)

        fhir_claim.diagnosis = diagnoses

    @classmethod
    def build_fhir_diagnosis(cls, diagnoses, icd_code, icd_type, reference_type):
        if icd_code is None:
            raise FHIRRequestProcessException(['ICD code cannot be null'])
        if icd_type is None:
            raise FHIRRequestProcessException(['ICD Type cannot be null'])

        claim_diagnosis_data =  {}
        claim_diagnosis_data['sequence'] = FhirUtils.get_next_array_sequential_id(diagnoses)
        claim_diagnosis_data['diagnosisReference'] = ConditionConverter\
            .build_fhir_resource_reference(icd_code, reference_type=reference_type)
        claim_diagnosis = ClaimDiagnosis(**claim_diagnosis_data)
        claim_diagnosis.type = [cls.build_codeable_concept(icd_type)]

        diagnoses.append(claim_diagnosis)

    @classmethod
    def build_imis_diagnoses(cls, imis_claim, fhir_claim, errors):
        diagnoses = fhir_claim.diagnosis
        if diagnoses:
            for diagnosis in diagnoses:
                diagnosis_type = cls.get_diagnosis_type(diagnosis)
                diagnosis_code = cls.get_diagnosis_code(diagnosis)
                if diagnosis_type == ImisClaimIcdTypes.ICD_0.value:
                    imis_claim.icd = cls.get_claim_diagnosis_by_code(diagnosis_code)
                    imis_claim.icd_code = diagnosis_code
                elif diagnosis_type == ImisClaimIcdTypes.ICD_1.value:
                    imis_claim.icd1_code = diagnosis_code
                    imis_claim.icd_1= cls.get_claim_diagnosis_by_code(diagnosis_code)
                elif diagnosis_type == ImisClaimIcdTypes.ICD_2.value:
                    imis_claim.icd_2 = cls.get_claim_diagnosis_by_code(diagnosis_code)
                    imis_claim.icd2_code = diagnosis_code
                elif diagnosis_type == ImisClaimIcdTypes.ICD_3.value:
                    imis_claim.icd_3 = cls.get_claim_diagnosis_by_code(diagnosis_code)
                    imis_claim.icd3_code = diagnosis_code
                elif diagnosis_type == ImisClaimIcdTypes.ICD_4.value:
                    imis_claim.icd_4 = cls.get_claim_diagnosis_by_code(diagnosis_code)
                    imis_claim.icd4_code = diagnosis_code
        cls.valid_condition(imis_claim.icd is None, gettext('Missing the main diagnosis for claim'), errors)

    @classmethod
    def get_diagnosis_type(cls, diagnosis):
        diagnosis_type = None
        type_concept = cls.get_first_diagnosis_type(diagnosis)
        if type_concept:
            if type_concept.coding:
                for item in type_concept.coding:
                    diagnosis_type = item.code
        return diagnosis_type

    @classmethod
    def get_first_diagnosis_type(cls, diagnosis):
        if diagnosis.type:
            return diagnosis.type[0] if diagnosis.type else  None
        else:
            return None
        
    @classmethod
    def get_claim_diagnosis_by_code(cls, icd_code):
        return Diagnosis.objects.get(code=icd_code)

    @classmethod
    def get_claim_diagnosis_code_by_id(cls, diagnosis_id):
        code = None
        if diagnosis_id is not None:
            diagnosis = DbManagerUtils.get_object_or_none(Diagnosis, pk=diagnosis_id)
            if diagnosis:
                code = diagnosis.code
        return code

    @classmethod
    def get_diagnosis_code(cls, diagnosis):
        code = None
        if diagnosis.diagnosisReference.reference:
            _, icd = diagnosis.diagnosisReference.reference.rsplit('/',1)
            code = icd

        return code

    @classmethod
    def build_fhir_total(cls, fhir_claim, imis_claim):
        total_claimed = imis_claim.claimed
        if not total_claimed:
            total_claimed = 0
        fhir_total = Money.construct()
        fhir_total.value = total_claimed
        if hasattr(core, 'currency'):
            fhir_total.currency = core.currency
        fhir_claim.total = fhir_total

    @classmethod
    def build_imis_total_claimed(cls, imis_claim, fhir_claim, errors):
        total_money = fhir_claim.total
        if total_money is not None:
            imis_claim.claimed = total_money.value
        cls.valid_condition(imis_claim.claimed is None,
                            gettext('Missing the value for `total` attribute'), errors)

    @classmethod
    def build_imis_claim_admin(cls, imis_claim, fhir_claim, errors):
        if fhir_claim.enterer:
            admin = PractitionerConverter.get_imis_obj_by_fhir_reference(fhir_claim.enterer)
            if admin:
                imis_claim.admin = admin
                imis_claim.claim_admin_code = admin.code
        cls.valid_condition(imis_claim.admin is None, gettext('Missing the enterer reference'), errors)

    @classmethod
    def build_fhir_type(cls, fhir_claim, imis_claim):
        if imis_claim.visit_type:
            fhir_claim.type = cls.build_simple_codeable_concept(imis_claim.visit_type)

    @classmethod
    def build_imis_visit_type(cls, imis_claim, fhir_claim):
        if fhir_claim.type:
            imis_claim.visit_type = fhir_claim.type.text

    @classmethod
    def build_fhir_supportingInfo(cls, fhir_claim, imis_claim):
        guarantee_id_code = R4ClaimConfig.get_fhir_claim_information_guarantee_id_code()
        cls.build_fhir_string_information(fhir_claim.supportingInfo, guarantee_id_code, imis_claim.guarantee_id)
        explanation_code = R4ClaimConfig.get_fhir_claim_information_explanation_code()
        cls.build_fhir_string_information(fhir_claim.supportingInfo, explanation_code, imis_claim.explanation)

    @classmethod
    def build_imis_supportingInfo(cls, imis_claim, fhir_claim):
        if fhir_claim.supportingInfo:
            for supportingInfo in fhir_claim.supportingInfo:
                category = supportingInfo.category
                if category and category.text == R4ClaimConfig.get_fhir_claim_information_guarantee_id_code():
                    imis_claim.guarantee_id = supportingInfo.valueString
                elif category and category.text == R4ClaimConfig.get_fhir_claim_information_explanation_code():
                    imis_claim.explanation = supportingInfo.valueString

    @classmethod
    def build_fhir_string_information(cls, claim_information, code, value_string):
        result = None
        if value_string:
            supportingInfo_concept = ClaimSupportingInfo.construct()
            supportingInfo_concept.sequence = FhirUtils.get_next_array_sequential_id(claim_information)
            supportingInfo_concept.category = cls.build_simple_codeable_concept(code)
            supportingInfo_concept.valueString = value_string
            if type(claim_information) is not list:
                claim_information = [supportingInfo_concept]
            else:
                claim_information.append(supportingInfo_concept)
            result = supportingInfo_concept
        return result

    @classmethod
    def build_fhir_items(cls, fhir_claim, imis_claim, reference_type):
        cls.build_items_for_imis_item(fhir_claim, imis_claim, reference_type)
        cls.build_items_for_imis_services(fhir_claim, imis_claim, reference_type)

    @classmethod
    def build_items_for_imis_item(cls, fhir_claim, imis_claim, reference_type):
        for item in imis_claim.items.filter(validity_to=None).all():
            if item:
                type = R4ClaimConfig.get_fhir_claim_item_code()
                cls.build_fhir_item(fhir_claim, item.item.code, type, item, reference_type)

    @classmethod
    def get_imis_items_for_claim(cls, imis_claim):
        items = []
        if imis_claim and imis_claim.id:
            items = ClaimItem.objects.filter(claim_id=imis_claim.id)
        return items

    @classmethod
    def build_fhir_item(cls, fhir_claim, code, item_type, item, reference_type):
        fhir_item = FHIRClaimItem.construct()
        fhir_item.sequence = FhirUtils.get_next_array_sequential_id(fhir_claim.item)
        unit_price = Money.construct()
        unit_price.value = item.price_asked
        if hasattr(core, 'currency'):
            unit_price.currency = core.currency
        fhir_item.unitPrice = unit_price
        fhir_quantity = Quantity.construct()
        fhir_quantity.value = item.qty_provided
        fhir_item.quantity = fhir_quantity
        fhir_item.productOrService = cls.build_simple_codeable_concept(code)
        fhir_item.category = cls.build_simple_codeable_concept(item_type)
        item_explanation_code = R4ClaimConfig.get_fhir_claim_item_explanation_code()
        information = cls.build_fhir_string_information(fhir_claim.supportingInfo, item_explanation_code, item.explanation)
        if information:
            if type(fhir_item.informationSequence) is not list:
                fhir_item.informationSequence = [information.sequence]
            else:
                fhir_item.informationSequence.append(information.sequence)

        extension = Extension.construct()

        if fhir_item.category.text == "item":
            medication = cls.build_medication_extension(extension, item, reference_type)
            if type(fhir_item.extension) is not list:
                fhir_item.extension = [medication]
            else:
                fhir_item.extension.append(medication)

        elif fhir_item.category.text == "service":
            activity_definition = cls.build_activity_definition_extension(extension, item, reference_type)
            if type(fhir_item.extension) is not list:
                fhir_item.extension = [activity_definition]
            else:
                fhir_item.extension.append(activity_definition)

        if type(fhir_claim.item) is not list:
            fhir_claim.item = [fhir_item]
        else:
            fhir_claim.item.append(fhir_item)

    @classmethod
    def build_items_for_imis_services(cls, fhir_claim, imis_claim, reference_type):
        for service in imis_claim.services.filter(validity_to=None).all():
            if service:
                type = R4ClaimConfig.get_fhir_claim_service_code()
                cls.build_fhir_item(fhir_claim, service.service.code, type, service, reference_type)

    @classmethod
    def get_imis_services_for_claim(cls, imis_claim):
        services = []
        if imis_claim and imis_claim.id:
            services = ClaimService.objects.filter(claim_id=imis_claim.id)
        return services

    @classmethod
    def build_medication_extension(cls, extension, item, reference_type):
        reference = Reference.construct()
        extension.valueReference = reference
        extension.url = "Medication"
        if item.item is None:
            raise FHIRRequestProcessException(['Cannot construct medication on  None (Item) '] )
        extension.valueReference = MedicationConverter\
            .build_fhir_resource_reference(item.item, reference_type=reference_type)
        return extension

    @classmethod
    def build_activity_definition_extension(cls, extension, service, reference_type):
        reference = Reference.construct()
        extension.valueReference = reference
        extension.url = "ActivityDefinition"
        if service.service is None:
            raise FHIRRequestProcessException(['Cannot construct activity on None (service) '] )
        extension.valueReference = ActivityDefinitionConverter\
            .build_fhir_resource_reference(service.service, reference_type=reference_type)
        return extension

    @classmethod
    def build_imis_submit_items_and_services(cls, imis_claim, fhir_claim):
        imis_items = []
        imis_services = []
        if fhir_claim.item:
            for item in fhir_claim.item:
                if item.category:
                    if item.category.text == R4ClaimConfig.get_fhir_claim_item_code():
                        cls.build_imis_submit_item(imis_items, item)
                    elif item.category.text == R4ClaimConfig.get_fhir_claim_service_code():
                        cls.build_imis_submit_service(imis_services, item)
        # added additional attributes which will be used to create ClaimRequest in serializer
        imis_claim.submit_items = imis_items
        imis_claim.submit_services = imis_services

    @classmethod
    def build_imis_submit_item(cls, imis_items, fhir_item):
        price_asked = cls.get_fhir_item_price_asked(fhir_item)
        qty_provided = cls.get_fhir_item_qty_provided(fhir_item)
        item_code = cls.get_fhir_item_code(fhir_item)
        if type(imis_items) is not list:
            imis_items = [ClaimItemSubmit(item_code, qty_provided, price_asked)]
        else:
            imis_items.append(ClaimItemSubmit(item_code, qty_provided, price_asked))

    @classmethod
    def build_imis_submit_service(cls, imis_services, fhir_item):
        price_asked = cls.get_fhir_item_price_asked(fhir_item)
        qty_provided = cls.get_fhir_item_qty_provided(fhir_item)
        service_code = cls.get_fhir_item_code(fhir_item)
        if type(imis_services) is not list:
            imis_services = [ClaimServiceSubmit(service_code, qty_provided, price_asked)]
        else:
            imis_services.append(ClaimServiceSubmit(service_code, qty_provided, price_asked))

    @classmethod
    def get_fhir_item_code(cls, fhir_item):
        item_code = None
        if fhir_item.productOrService:
            item_code = fhir_item.productOrService.text
        return item_code

    @classmethod
    def get_fhir_item_qty_provided(cls, fhir_item):
        qty_provided = None
        if fhir_item.quantity:
            qty_provided = fhir_item.quantity.value
        return qty_provided

    @classmethod
    def get_fhir_item_price_asked(cls, fhir_item):
        price_asked = None
        if fhir_item.unitPrice:
            price_asked = fhir_item.unitPrice.value
        return price_asked

    @classmethod
    def build_fhir_provider(cls, fhir_claim, imis_claim, reference_type):
        if imis_claim.admin is not None:
            fhir_claim.provider = PractitionerRoleConverter\
                .build_fhir_resource_reference(imis_claim.admin, reference_type=reference_type)

    @classmethod
    def build_imis_adjuster(cls, imis_claim, fhir_claim, errors):
        adjuster = fhir_claim.provider
        if not cls.valid_condition(adjuster is None,
                                   gettext('Missing claim `adjuster` attribute'), errors):
            imis_claim.adjuster = adjuster

    @classmethod
    def build_fhir_use(cls, fhir_claim):
        fhir_claim['use'] = "claim"

    @classmethod
    def build_fhir_priority(cls, fhir_claim):
        fhir_claim.priority = cls.build_codeable_concept("normal", None, None)

    @classmethod
    def build_fhir_status(cls, fhir_claim):
        fhir_claim['status'] = "active"

    @classmethod
    def build_fhir_insurance(cls, fhir_claim, imis_claim, reference_type):
        claim_insurance_data = {}
        claim_insurance_data["sequence"] = 1
        claim_insurance_data["focal"] = True
        fhir_insurance = ClaimInsurance(**claim_insurance_data)
        imis_insuree_policy  = imis_claim.insuree.insuree_policies.all()
        # fixme get latest policy, not the one active at the claim
        for pol in imis_insuree_policy:
            policy = pol.policy
            fhir_insurance.coverage = CoverageConverter\
                .build_fhir_resource_reference(policy, reference_type=reference_type)

        if fhir_insurance.coverage is None:
            coverage_reference = Reference.construct()
            coverage_reference.reference = "Coverage"
            fhir_insurance.coverage = coverage_reference

        if fhir_claim.insurance is not list:
            fhir_claim.insurance = [fhir_insurance]
        else:
            fhir_claim.insurance.append(fhir_insurance)

    @classmethod
    def build_imis_attachments(cls, imis_claim: Claim, fhir_claim: FHIRClaim):
        supporting_info = fhir_claim.supportingInfo
        if not hasattr(imis_claim, 'claim_attachments'):
            imis_claim.claim_attachments = []

        for next_attachment in supporting_info:
            if next_attachment.category.text == R4ClaimConfig.get_fhir_claim_attachment_code():
                claim_attachment = cls.build_attachment_from_value(next_attachment.valueAttachment)
                if imis_claim.claim_attachments is not list:
                    imis_claim.claim_attachments = [claim_attachment]
                else:
                    imis_claim.claim_attachments.append(claim_attachment)

    @classmethod
    def build_fhir_attachments(cls, fhir_claim, imis_claim):
        attachments = ClaimAttachment.objects.filter(claim=imis_claim)

        if not fhir_claim.supportingInfo:
            fhir_claim.supportingInfo = []

        for attachment in attachments:
            supporting_info_element = cls.build_attachment_supporting_info_element(attachment)
            if fhir_claim.supportingInfo is not list:
                fhir_claim.supportingInfo = [supporting_info_element]
            else:
                fhir_claim.supportingInfo.append(supporting_info_element)

    @classmethod
    def build_attachment_supporting_info_element(cls, imis_attachment):
        supporting_info_element = ClaimSupportingInfo.construct()

        supporting_info_element.category = cls.build_attachment_supporting_info_category()
        supporting_info_element.valueAttachment = cls.build_fhir_value_attachment(imis_attachment)
        return supporting_info_element

    @classmethod
    def build_attachment_supporting_info_category(cls):
        category_code = R4ClaimConfig.get_fhir_claim_attachment_code()
        system = R4ClaimConfig.get_fhir_claim_attachment_system()
        category = cls.build_codeable_concept(category_code, system, category_code)
        category.coding[0].display = category_code.capitalize()
        return category

    @classmethod
    def build_fhir_value_attachment(cls, imis_attachment):
        attachment = Attachment.construct()
        attachment.creation = imis_attachment.date.isoformat()
        attachment.data = cls.get_attachment_content(imis_attachment)
        attachment.contentType = imis_attachment.mime
        attachment.title = imis_attachment.filename
        return attachment

    @classmethod
    def get_attachment_content(cls, imis_attachment):
        file_root = ClaimConfig.claim_attachments_root_path

        if file_root and imis_attachment.url:
            with open('%s/%s' % (ClaimConfig.claim_attachments_root_path, imis_attachment.url), "rb") as file:
                return base64.b64encode(file.read())
        elif not imis_attachment.url and imis_attachment.document:
            return imis_attachment.document
        else:
            return None

    @classmethod
    def build_attachment_from_value(cls, valueAttachment: Attachment):
        allowed_mime_regex = R4ClaimConfig.get_allowed_fhir_claim_attachment_mime_types_regex()
        mime_validation = re.compile(allowed_mime_regex, re.IGNORECASE)

        if not mime_validation.match(valueAttachment.contentType):
            raise ValueError(F'Mime type {valueAttachment.contentType} not allowed')

        if valueAttachment.hash:
            cls.validateHash(valueAttachment.hash, valueAttachment.data)

        attachment_data = {
            'title': valueAttachment.title,
            'filename': valueAttachment.title,
            'document': valueAttachment.data,
            'mime': valueAttachment.contentType,
            'date': TimeUtils.str_to_date(valueAttachment.creation)
        }
        return attachment_data

    @classmethod
    def validateHash(cls, expected_hash, data):
        actual_hash = hashlib.sha1(data.encode('utf-8')).hexdigest()
        if actual_hash.casefold() != expected_hash.casefold():
            raise ValueError('Hash for data file is incorrect')

    @classmethod
    def _build_facility_reference(cls, imis_claim, reference_type):
        if imis_claim.health_facility is None:
            raise FHIRRequestProcessException([
                'Cannot construct a %s claim if HF is None' % imis_claim.uuid
            ])
        return HealthcareServiceConverter\
            .build_fhir_resource_reference(imis_claim.health_facility,
                                           type='Location',
                                           display=imis_claim.health_facility.code,
                                           reference_type=reference_type)

    @classmethod
    def _build_patient_reference(cls, imis_claim, reference_type):
        if imis_claim.insuree is None:
            raise FHIRRequestProcessException([
                'Cannot construct a %s claim if Insuree is None' % imis_claim.uuid
            ])
        return PatientConverter\
            .build_fhir_resource_reference(imis_claim.insuree,
                                           type='Patient',
                                           display=imis_claim.insuree.chf_id,
                                           reference_type=reference_type)

    @classmethod
    def _build_practitioner_reference(cls, imis_claim, reference_type):
        if imis_claim.admin is None:
            raise FHIRRequestProcessException([
                F'Failed to create FHIR instance for claim {imis_claim.uuid}: Claim Admin field not found'
            ])
        else:
            return PractitionerConverter\
                .build_fhir_resource_reference(imis_claim.admin,
                                               type='Practitioner',
                                               reference_type=reference_type)
