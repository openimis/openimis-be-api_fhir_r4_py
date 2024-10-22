import base64
import hashlib
import re
from urllib.parse import urljoin

from typing import Type

from claim.services import ClaimElementSubmit
from claim.apps import ClaimConfig
from claim.models import Claim, ClaimItem, ClaimService, ClaimAttachment

from api_fhir_r4.containedResources.converterUtils import get_from_contained_or_by_reference
from api_fhir_r4.mapping.claimMapping import ClaimPriorityMapping, ClaimVisitTypeMapping
from medical.models import Diagnosis
from django.utils.translation import gettext as _

from api_fhir_r4.configurations import R4IdentifierConfig, R4ClaimConfig, GeneralConfiguration
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin, MedicationConverter, \
    ActivityDefinitionConverter
from api_fhir_r4.converters.patientConverter import PatientConverter
from api_fhir_r4.converters.healthFacilityOrganisationConverter import HealthFacilityOrganisationConverter
from api_fhir_r4.converters.claimAdminPractitionerConverter import ClaimAdminPractitionerConverter
from api_fhir_r4.models import ClaimV2 as FHIRClaim, ClaimInsuranceV2 as ClaimInsurance
from fhir.resources.R4B.attachment import Attachment
from fhir.resources.R4B.period import Period
from fhir.resources.R4B.claim import ClaimDiagnosis, ClaimSupportingInfo, ClaimItem as FHIRClaimItem
from core.utils import filter_validity
from api_fhir_r4.utils import TimeUtils, FhirUtils, DbManagerUtils

import logging
logger = logging.getLogger('openimis.' + __name__)

class ClaimConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_claim, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_claim = cls.build_fhir_obj_with_required_fields(imis_claim)
        cls.build_fhir_identifiers(fhir_claim, imis_claim)
        cls.build_fhir_pk(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_provider(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_patient(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_enterer(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_type(fhir_claim, imis_claim)
        cls.build_fhir_priority(fhir_claim)
        cls.build_fhir_insurance(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_billable_period(fhir_claim, imis_claim)
        cls.build_fhir_diagnoses(fhir_claim, imis_claim)
        cls.build_fhir_total(fhir_claim, imis_claim)
        cls.build_fhir_items(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_supporting_info(fhir_claim, imis_claim)
        cls.build_fhir_attachments(fhir_claim, imis_claim)
        return fhir_claim

    @classmethod
    def to_imis_obj(cls, fhir_claim, audit_user_id):
        errors = []
        fhir_claim = FHIRClaim(**fhir_claim)
        imis_claim = Claim()
        imis_claim.audit_user_id = audit_user_id
        cls.build_imis_date_claimed(imis_claim, fhir_claim, errors)
        cls.build_imis_health_facility(errors, fhir_claim, imis_claim, audit_user_id=audit_user_id)
        cls.build_imis_identifier(imis_claim, fhir_claim, errors)
        cls.build_imis_patient(imis_claim, fhir_claim, errors, audit_user_id=audit_user_id)
        cls.build_imis_date_range(imis_claim, fhir_claim, errors)
        cls.build_imis_diagnoses(imis_claim, fhir_claim, errors)
        cls.build_imis_total_claimed(imis_claim, fhir_claim, errors)
        cls.build_imis_claim_admin(imis_claim, fhir_claim, errors, audit_user_id=audit_user_id)
        cls.build_imis_visit_type(imis_claim, fhir_claim, errors)
        cls.build_imis_supporting_info(imis_claim, fhir_claim, errors)
        cls.build_imis_submit_items_and_services(imis_claim, fhir_claim, errors, audit_user_id)
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
    def get_reference_obj_code(cls, imis_claim):
        return imis_claim.code

    @classmethod
    def get_fhir_resource_type(cls):
        return FHIRClaim

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        return DbManagerUtils.get_object_or_none(
            Claim,
            **cls.get_database_query_id_parameteres_from_reference(reference))


    @classmethod
    def build_imis_date_claimed(cls, imis_claim, fhir_claim, errors):
        if fhir_claim.created:
            imis_claim.date_claimed = TimeUtils.str_to_date(fhir_claim.created)
        cls.valid_condition(not imis_claim.date_claimed, _('Missing `created` attribute'), errors)

    @classmethod
    def build_fhir_identifiers(cls, fhir_claim, imis_claim):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_claim)
        fhir_claim.identifier = identifiers

    @classmethod
    def build_imis_identifier(cls, imis_claim, fhir_claim, errors):
        value = cls.get_fhir_identifier_by_code(fhir_claim.identifier, cls.get_fhir_code_identifier_type())
        if value:
            imis_claim.code = value
        cls.valid_condition(not imis_claim.code, _('Missing or invalid `identifier` attribute'), errors)

    @classmethod
    def build_fhir_obj_with_required_fields(cls, imis_claim):
        fhir_claim_dict = {}
        cls.build_fhir_status(fhir_claim_dict)
        cls.build_fhir_use(fhir_claim_dict)
        cls.build_fhir_created(fhir_claim_dict, imis_claim)
        return FHIRClaim(**fhir_claim_dict)

    @classmethod
    def build_imis_patient(cls, imis_claim, fhir_claim, errors, audit_user_id):
        insuree = get_from_contained_or_by_reference(
            fhir_claim.patient, fhir_claim.contained, PatientConverter, audit_user_id)
        if insuree:
            imis_claim.insuree = insuree
            imis_claim.insuree_chf_id = insuree.chf_id
        cls.valid_condition(not imis_claim.insuree, _('Missing or invalid `patient` reference'), errors)

    @classmethod
    def build_imis_health_facility(cls, errors, fhir_claim, imis_claim, audit_user_id):
        health_facility = get_from_contained_or_by_reference(
            fhir_claim.provider, fhir_claim.contained, HealthFacilityOrganisationConverter, audit_user_id
        )
        if health_facility:
            imis_claim.health_facility = health_facility
            imis_claim.health_facility_code = health_facility.code
        cls.valid_condition(not imis_claim.health_facility, _('Missing or invalid `provider` reference'), errors)

    @classmethod
    def build_fhir_billable_period(cls, fhir_claim, imis_claim):
        billable_period = Period.construct()
        billable_period.start = imis_claim.date_from.isoformat()
        if imis_claim.date_to:
            billable_period.end = imis_claim.date_to.isoformat()
        else:
            billable_period.end = billable_period.start
        fhir_claim.billablePeriod = billable_period

    @classmethod
    def build_imis_date_range(cls, imis_claim, fhir_claim, errors):
        billable_period = fhir_claim.billablePeriod
        if billable_period and hasattr(billable_period, "start"):
            if billable_period.start:
                imis_claim.date_from = TimeUtils.str_to_date(billable_period.start)
            if billable_period.end:
                imis_claim.date_to = TimeUtils.str_to_date(billable_period.end)
        cls.valid_condition(not imis_claim.date_from, _("Missing or invalid 'billable_period' attribute"), errors)

    @classmethod
    def build_fhir_diagnoses(cls, fhir_claim, imis_claim):
        fhir_diagnoses = []
        imis_diagnoses = [imis_claim.icd, imis_claim.icd_1, imis_claim.icd_2, imis_claim.icd_3, imis_claim.icd_4]
        for icd in imis_diagnoses:
            if icd:
                cls.build_fhir_diagnosis(fhir_diagnoses, icd)
        fhir_claim.diagnosis = fhir_diagnoses

    @classmethod
    def build_fhir_diagnosis(cls, diagnoses, icd):
        base = GeneralConfiguration.get_system_base_url()
        system = urljoin(base, R4ClaimConfig.get_fhir_claim_diagnosis_system())
        diagnosis_codeable_concept = cls.build_codeable_concept(icd.code, system=system, display=icd.name)
        claim_diagnosis_data = {'sequence': FhirUtils.get_next_array_sequential_id(diagnoses),
                                'diagnosisCodeableConcept': diagnosis_codeable_concept.dict()}
        diagnoses.append(ClaimDiagnosis(**claim_diagnosis_data))

    @classmethod
    def build_imis_diagnoses(cls, imis_claim, fhir_claim, errors):
        diagnoses = fhir_claim.diagnosis
        icd_fields_suffixes = [["", "_code"], ["_1", "1_code"], ["_2", "2_code"], ["_3", "3_code"], ["_4", "4_code"]]
        if diagnoses:
            for diagnosis, field_suffix in zip(diagnoses, icd_fields_suffixes):
                diagnosis_code = cls.get_imis_diagnosis_code(diagnosis)
                diagnosis_obj = cls.get_imis_diagnosis_by_code(diagnosis_code)
                setattr(imis_claim, "icd" + field_suffix[0], diagnosis_obj)
                setattr(imis_claim, "icd" + field_suffix[1], diagnosis_obj.code)
        cls.valid_condition(imis_claim.icd is None, _('Missing or invalid `diagnosis` attribute'), errors)

    @classmethod
    def get_imis_diagnosis_by_code(cls, icd_code):
        return Diagnosis.objects.get(code=icd_code, *filter_validity())

    @classmethod
    def get_imis_diagnosis_code(cls, diagnosis):
        coding = cls.get_first_coding_from_codeable_concept(diagnosis.diagnosisCodeableConcept)
        return coding.code

    @classmethod
    def build_fhir_total(cls, fhir_claim, imis_claim):
        fhir_claim.total = cls.build_fhir_money(imis_claim.claimed)

    @classmethod
    def build_imis_total_claimed(cls, imis_claim, fhir_claim, errors):
        total_money = fhir_claim.total
        if total_money is not None:
            imis_claim.claimed = total_money.value
        cls.valid_condition(not imis_claim.claimed, _('Missing `total` attribute'), errors)

    @classmethod
    def build_imis_claim_admin(cls, imis_claim, fhir_claim, errors, audit_user_id):
        admin = get_from_contained_or_by_reference(
            fhir_claim.enterer, fhir_claim.contained, ClaimAdminPractitionerConverter, audit_user_id
        )
        if admin:
            imis_claim.admin = admin
            imis_claim.claim_admin_code = admin.code
        cls.valid_condition(imis_claim.admin is None, _('Missing or invalid `enterer` reference'), errors)

    @classmethod
    def build_fhir_type(cls, fhir_claim, imis_claim):
        mapping = ClaimVisitTypeMapping.fhir_claim_visit_type_coding[imis_claim.visit_type]
        fhir_claim.type = cls.build_codeable_concept_from_coding(cls.build_fhir_mapped_coding(mapping))

    @classmethod
    def build_imis_visit_type(cls, imis_claim, fhir_claim, errors):
        if fhir_claim.type:
            claim_type = cls.get_first_coding_from_codeable_concept(fhir_claim.type)
            if hasattr(claim_type, "code"):
                imis_claim.visit_type = claim_type.code
        cls.valid_condition(not imis_claim.visit_type, _('Missing or invalid `type` attribute'), errors)

    @classmethod
    def build_fhir_supporting_info(cls, fhir_claim, imis_claim):
        supporting_info = []
        guarantee_id_code = R4ClaimConfig.get_fhir_claim_information_guarantee_id_code()
        cls.build_fhir_string_information(supporting_info, guarantee_id_code, imis_claim.guarantee_id)
        explanation_code = R4ClaimConfig.get_fhir_claim_information_explanation_code()
        cls.build_fhir_string_information(supporting_info, explanation_code, imis_claim.explanation)
        fhir_claim.supportingInfo = supporting_info

    @classmethod
    def build_imis_supporting_info(cls, imis_claim, fhir_claim, errors):
        if not hasattr(imis_claim, "claim_attachments") or imis_claim.claim_attachments is not list:
            imis_claim.claim_attachments = []
        if fhir_claim.supportingInfo:
            for supporting_info in fhir_claim.supportingInfo:
                category_coding = cls.get_first_coding_from_codeable_concept(supporting_info.category)
                category = category_coding.code
                if category == R4ClaimConfig.get_fhir_claim_information_guarantee_id_code():
                    imis_claim.guarantee_id = supporting_info.valueString
                elif category == R4ClaimConfig.get_fhir_claim_information_explanation_code():
                    imis_claim.explanation = supporting_info.valueString
                elif category == R4ClaimConfig.get_fhir_claim_attachment_code():
                    claim_attachment = cls.build_attachment_from_value(supporting_info.valueAttachment)
                    imis_claim.claim_attachments.append(claim_attachment)
                else:
                    cls.valid_condition(True, _('Unknown supporting info category: `%s`') % category, errors)

    @classmethod
    def build_fhir_string_information(cls, supporting_info, code, value_string):
        if value_string:
            supporting_info_entry = ClaimSupportingInfo.construct()
            supporting_info_entry.sequence = FhirUtils.get_next_array_sequential_id(supporting_info)
            base = GeneralConfiguration.get_system_base_url()
            system = urljoin(base, R4ClaimConfig.get_fhir_claim_supporting_info_system())
            category = cls.build_codeable_concept(code, system)
            supporting_info_entry.category = category
            supporting_info_entry.valueString = value_string
            supporting_info.append(supporting_info_entry)

    @classmethod
    def build_fhir_items(cls, fhir_claim, imis_claim, reference_type):
        fhir_claim.item = []
        cls.build_fhir_items_for_imis_items(fhir_claim, imis_claim, reference_type)
        cls.build_fhir_items_for_imis_services(fhir_claim, imis_claim, reference_type)

    @classmethod
    def build_fhir_items_for_imis_items(cls, fhir_claim, imis_claim, reference_type):
        for claim_item in imis_claim.items.filter(*filter_validity()):
            if claim_item:
                item_type = R4ClaimConfig.get_fhir_claim_item_code()
                cls.build_fhir_item(fhir_claim, claim_item.item.code, item_type, claim_item, reference_type)

    @classmethod
    def get_imis_items_for_claim(cls, imis_claim):
        items = []
        if imis_claim and imis_claim.id:
            items = ClaimItem.objects.filter(claim_id=imis_claim.id)
        return items

    @classmethod
    def build_fhir_item(cls, fhir_claim, code, item_type, claim_item, reference_type):
        fhir_item = FHIRClaimItem.construct()
        fhir_item.sequence = FhirUtils.get_next_array_sequential_id(fhir_claim.item)
        fhir_item.unitPrice = cls.build_fhir_money(claim_item.price_asked)
        fhir_item.quantity = cls.build_fhir_quantity(claim_item.qty_provided)
        fhir_item.productOrService = cls.build_simple_codeable_concept(code)
        fhir_item.category = cls.build_simple_codeable_concept(item_type)
        fhir_item.extension = []

        if item_type == R4ClaimConfig.get_fhir_claim_item_code():
            medication = cls.build_medication_extension(claim_item, reference_type)
            fhir_item.extension.append(medication)

        elif item_type == R4ClaimConfig.get_fhir_claim_service_code():
            activity_definition = cls.build_activity_definition_extension(claim_item, reference_type)
            fhir_item.extension.append(activity_definition)

        fhir_claim.item.append(fhir_item)

    @classmethod
    def build_fhir_items_for_imis_services(cls, fhir_claim, imis_claim, reference_type):
        for claim_service in imis_claim.services.filter(*filter_validity()):
            if claim_service:
                item_type = R4ClaimConfig.get_fhir_claim_service_code()
                cls.build_fhir_item(fhir_claim, claim_service.service.code, item_type, claim_service, reference_type)

    @classmethod
    def get_imis_services_for_claim(cls, imis_claim):
        services = []
        if imis_claim and imis_claim.id:
            services = ClaimService.objects.filter(claim_id=imis_claim.id)
        return services

    @classmethod
    def build_medication_extension(cls, item, reference_type):
        base = GeneralConfiguration.get_system_base_url()
        url = urljoin(base, R4ClaimConfig.get_fhir_item_reference_extension_system())
        reference = cls.build_fhir_resource_reference(item.item, type='Medication', reference_type=reference_type)
        return cls.build_fhir_reference_extension(reference, url)

    @classmethod
    def build_activity_definition_extension(cls, service, reference_type):
        base = GeneralConfiguration.get_system_base_url()
        url = urljoin(base, R4ClaimConfig.get_fhir_item_reference_extension_system())
        reference = cls.build_fhir_resource_reference(service.service, type='ActivityDefinition',
                                                      reference_type=reference_type)
        return cls.build_fhir_reference_extension(reference, url)

    @classmethod
    def build_imis_submit_items_and_services(cls, imis_claim, fhir_claim, errors, audit_user_id):
        imis_items = []
        imis_services = []
        if fhir_claim.item:
            for item in fhir_claim.item:
                category = item.category.text
                if category == R4ClaimConfig.get_fhir_claim_item_code():
                    cls.build_imis_submit_item(imis_items, item, fhir_claim, audit_user_id)
                elif category == R4ClaimConfig.get_fhir_claim_service_code():
                    cls.build_imis_submit_service(imis_services, item, fhir_claim, audit_user_id)
                else:
                    cls.valid_condition(True, _('Unknown item category: `%s`') % category, errors)

        # added additional attributes which will be used to create ClaimRequest in serializer
        imis_claim.submit_items = imis_items
        imis_claim.submit_services = imis_services

    @classmethod
    def build_imis_submit_item(cls, imis_items, fhir_item, fhir_claim, audit_user_id):
        item = cls.__get_provision_from_contained_or_reference(
                fhir_item, fhir_claim,
                MedicationConverter,
                audit_user_id)
        claim_item = ClaimItem(
            qty_provided=cls.get_fhir_item_qty_provided(fhir_item),
            price_asked=cls.get_fhir_item_price_asked(fhir_item),
            item=item
        )
        claim_item.code = item.code
        imis_items.append(claim_item)

    @classmethod
    def build_imis_submit_service(cls, imis_services, fhir_item, fhir_claim, audit_user_id):
        claim_service = ClaimService(
            qty_provided=cls.get_fhir_item_qty_provided(fhir_item),
            price_asked=cls.get_fhir_item_price_asked(fhir_item),
            service=cls.__get_provision_from_contained_or_reference(
                fhir_item, fhir_claim,
                ActivityDefinitionConverter,
                audit_user_id)
        )
        claim_service.code = claim_service.service.code
        imis_services.append(claim_service)

    @classmethod
    def __get_provision_from_contained_or_reference(cls, fhir_provision, fhir_claim, converter, audit_user_id):
        # Items and services are referenced by extension with ValueReference
        reference = fhir_provision.extension[0].valueReference
        return get_from_contained_or_by_reference(
            reference, fhir_claim.contained, converter, audit_user_id)

    @classmethod
    def _get_imis_claim_provision(cls, fhir_item, submission_type: Type[ClaimElementSubmit]):
        price_asked = cls.get_fhir_item_price_asked(fhir_item)
        quantity = cls.get_fhir_item_qty_provided(fhir_item)
        code = cls.get_fhir_item_code(fhir_item)
        return submission_type(code, quantity, price_asked).to_claim_provision()

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
    def build_fhir_use(cls, fhir_claim_dict):
        fhir_claim_dict['use'] = "claim"

    @classmethod
    def build_fhir_priority(cls, fhir_claim):
        mapping = ClaimPriorityMapping.fhir_priority_coding['normal']
        fhir_claim.priority = cls.build_codeable_concept_from_coding(cls.build_fhir_mapped_coding(mapping))

    @classmethod
    def build_fhir_status(cls, fhir_claim_dict):
        fhir_claim_dict['status'] = "active"

    @classmethod
    def build_fhir_created(cls, fhir_claim_dict, imis_claim):
        fhir_claim_dict['created'] = imis_claim.date_claimed.isoformat()

    @classmethod
    def build_fhir_insurance(cls, fhir_claim, imis_claim, reference_type):
        policies = list(imis_claim.insuree.insuree_policies.all())
        if policies:
            sorted_by_enrol = sorted(list(policies), key=lambda x: x.effective_date, reverse=True)
            latest = sorted_by_enrol[0]
            claim_insurance_data = {'focal': True, 'sequence': 1}
            insurance = ClaimInsurance(**claim_insurance_data)
            insurance.coverage = cls.build_fhir_resource_reference(latest.policy, type="Coverage",
                                                                   reference_type=reference_type)
            fhir_claim.insurance = [insurance]

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
    def build_fhir_provider(cls, fhir_claim, imis_claim, reference_type):
        fhir_claim.provider = cls.build_fhir_resource_reference(imis_claim.health_facility,
                                                                type='Organization',
                                                                display=imis_claim.health_facility.code,
                                                                reference_type=reference_type)

    @classmethod
    def build_fhir_patient(cls, fhir_claim, imis_claim, reference_type):
        fhir_claim.patient = cls.build_fhir_resource_reference(imis_claim.insuree,
                                                               type='Patient',
                                                               display=imis_claim.insuree.chf_id,
                                                               reference_type=reference_type)

    @classmethod
    def build_fhir_enterer(cls, fhir_claim, imis_claim, reference_type):
        fhir_claim.enterer = cls.build_fhir_resource_reference(imis_claim.admin,
                                                               type='Practitioner',
                                                               display=imis_claim.admin.code,
                                                               reference_type=reference_type)
