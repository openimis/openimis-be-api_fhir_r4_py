import datetime

from claim.models import Feedback, ClaimItem, ClaimService, Claim
from django.db.models import Subquery
from location.models import HealthFacility
from medical.models import Item, Service, Diagnosis
import core

from api_fhir_r4.configurations import R4ClaimConfig
from api_fhir_r4.converters import BaseFHIRConverter, CommunicationRequestConverter, ReferenceConverterMixin
from api_fhir_r4.converters.claimConverter import ClaimConverter
from api_fhir_r4.converters.patientConverter import PatientConverter
from api_fhir_r4.converters.healthcareServiceConverter import HealthcareServiceConverter
from api_fhir_r4.converters.medicationConverter import MedicationConverter
from api_fhir_r4.converters.conditionConverter import ConditionConverter
from api_fhir_r4.exceptions import FHIRRequestProcessException
from api_fhir_r4.models import ClaimResponseV2 as ClaimResponse, ClaimV2 as FHIRClaim
from api_fhir_r4.models.imisModelEnums import ImisClaimIcdTypes
from fhir.resources.money import Money
from fhir.resources.claimresponse import ClaimResponseError, ClaimResponseItem, ClaimResponseItemAdjudication, \
    ClaimResponseProcessNote, ClaimResponseTotal, ClaimResponsePayment
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference
from fhir.resources.extension import Extension
from fhir.resources.period import Period
from api_fhir_r4.utils import TimeUtils, FhirUtils


class ClaimResponseConverter(BaseFHIRConverter):

    @classmethod
    def to_fhir_obj(cls, imis_claim, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_claim_response = {}
        fhir_claim_response["created"] = TimeUtils.date().isoformat()
        cls.build_fhir_status(fhir_claim_response, imis_claim)
        cls.build_fhir_outcome(fhir_claim_response, imis_claim)
        cls.build_fhir_use(fhir_claim_response)
        fhir_claim_response = ClaimResponse(**fhir_claim_response)
        fhir_claim_response.request = ClaimConverter.build_fhir_resource_reference(imis_claim, reference_type=reference_type)
        cls.build_fhir_pk(fhir_claim_response, imis_claim, reference_type)
        ClaimConverter.build_fhir_identifiers(fhir_claim_response, imis_claim)
        cls.build_fhir_errors(fhir_claim_response, imis_claim)
        cls.build_fhir_items(fhir_claim_response, imis_claim, reference_type)
        cls.build_patient_reference(fhir_claim_response, imis_claim, reference_type)
        cls.build_fhir_total(fhir_claim_response, imis_claim)
        cls.build_fhir_communication_request_reference(fhir_claim_response, imis_claim, reference_type)
        cls.build_fhir_type(fhir_claim_response, imis_claim)
        cls.build_fhir_insurer(fhir_claim_response, imis_claim)
        cls.build_fhir_requestor(fhir_claim_response, imis_claim, reference_type)
        cls.build_fhir_billable_period(fhir_claim_response, imis_claim)
        cls.build_fhir_diagnoses(fhir_claim_response, imis_claim, reference_type)
        cls.build_fhir_adjustment(fhir_claim_response, imis_claim)
        return fhir_claim_response
               
    @classmethod
    def to_imis_obj(cls, fhir_claim_response, audit_user_id):
        errors = []
        fhir_claim_response = ClaimResponse(**fhir_claim_response)
        imis_claim = cls.get_imis_claim_from_response(fhir_claim_response)
        cls.build_imis_outcome(imis_claim, fhir_claim_response)
        cls.build_imis_errors(imis_claim, fhir_claim_response)
        cls.build_imis_items(imis_claim, fhir_claim_response)
        cls.build_imis_communication_request_reference(imis_claim, fhir_claim_response)
        cls.build_imis_type(imis_claim, fhir_claim_response)
        cls.build_imis_status(imis_claim, fhir_claim_response)
        cls.build_imis_requestor(imis_claim, fhir_claim_response)
        cls.build_imis_billable_period(imis_claim, fhir_claim_response)
        cls.build_imis_diagnoses(imis_claim, fhir_claim_response)
        cls.build_imis_adjustment(imis_claim, fhir_claim_response)
        return imis_claim

    @classmethod
    def get_reference_obj_uuid(cls, imis_claim):
        return imis_claim.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_claim):
        return imis_claim.id

    @classmethod
    def get_reference_obj_code(cls, imis_claim):
        return imis_claim.code

    @classmethod
    def build_fhir_outcome(cls, fhir_claim_response, imis_claim):
        code = imis_claim.status
        if code is not None:
            display = cls.get_status_display_by_code(code)
            fhir_claim_response["outcome"] = display

    @classmethod
    def build_imis_outcome(cls, imis_claim, fhir_claim_response):
        if fhir_claim_response.outcome is not None:
            status_code = cls.get_status_code_by_display(fhir_claim_response.outcome)
            imis_claim.status = status_code

    @classmethod
    def get_imis_claim_from_response(cls, fhir_claim_response):
        claim_uuid = fhir_claim_response.id
        try:
            return Claim.objects.get(uuid=claim_uuid)
        except Claim.DoesNotExit:
            raise FHIRRequestProcessException(F"Claim Response cannot be created from scratch, "
                                              f"IMIS instance for reference {claim_uuid} was not found.")

    _CODE_DISPLAY_STATUS = {
        1: R4ClaimConfig.get_fhir_claim_status_rejected_code(),
        2: R4ClaimConfig.get_fhir_claim_status_entered_code(),
        4: R4ClaimConfig.get_fhir_claim_status_checked_code(),
        8: R4ClaimConfig.get_fhir_claim_status_processed_code(),
        16: R4ClaimConfig.get_fhir_claim_status_valuated_code()
    }

    @classmethod
    def get_status_display_by_code(cls, code):
        display = cls._CODE_DISPLAY_STATUS.get(code, None)
        return display

    @classmethod
    def get_status_code_by_display(cls, claim_response_display):
        for code, display in cls._CODE_DISPLAY_STATUS.items():
            if display == claim_response_display:
                return code
        return None

    @classmethod
    def build_fhir_errors(cls, fhir_claim_response, imis_claim):
        rejection_reason = imis_claim.rejection_reason
        if rejection_reason:
            fhir_error = ClaimResponseError.construct()
            fhir_error.code = cls.build_codeable_concept(str(rejection_reason))
            if type(fhir_claim_response.error) is not list:
                fhir_claim_response.error = [fhir_error]
            else:
                fhir_claim_response.error.append(fhir_error)

    @classmethod
    def build_imis_errors(cls, imis_claim, fhir_claim_response: ClaimResponse):
        fhir_error = fhir_claim_response.error
        if fhir_error:
            error = fhir_error[0].code
            rejection_reason_str = cls.get_first_coding_from_codeable_concept(error)
            imis_claim.rejection_reason = int(rejection_reason_str.code)

    @classmethod
    def build_fhir_request_reference(cls, fhir_claim_response, imis_claim, reference_type):
        feedback = cls.get_imis_claim_feedback(imis_claim)
        if feedback:
            reference = CommunicationRequestConverter\
                .build_fhir_resource_reference(feedback, reference_type=reference_type)
            if fhir_claim_response.communicationRequest is not list:
                fhir_claim_response.communicationRequest = [reference]
            else:
                fhir_claim_response.communicationRequest.append(reference)

    @classmethod
    def get_imis_claim_feedback(cls, imis_claim):
        try:
            feedback = imis_claim.feedback
        except Feedback.DoesNotExist:
            feedback = None
        return feedback

    @classmethod
    def build_patient_reference(cls, fhir_claim_response, imis_claim, reference_type):
        fhir_claim_response.patient = PatientConverter\
            .build_fhir_resource_reference(imis_claim.insuree, reference_type=reference_type)

    @classmethod
    def build_fhir_total(cls, fhir_claim_response, imis_claim):
        #valuated = cls.build_fhir_total_valuated(imis_claim)
        #reinsured = cls.build_fhir_total_reinsured(imis_claim)
        approved = cls.build_fhir_total_approved(imis_claim)
        claimed = cls.build_fhir_total_claimed(imis_claim)

        # if valuated.amount.value is None and reinsured.amount.value is None and \
        #         approved.amount.value is None and claimed.amount.value is not None:
        #     fhir_claim_response.total = [claimed]
        #
        # elif valuated.amount.value is None and reinsured.amount.value is None and \
        #         approved.amount.value is not None and claimed.amount.value is not None:
        #     fhir_claim_response.total = [approved, claimed]
        #
        # elif valuated.amount.value is None and reinsured.amount.value is not None and \
        #         approved.amount.value is not None and claimed.amount.value is not None:
        #     fhir_claim_response.total = [reinsured, approved, claimed]
        #
        # else:
        #     fhir_claim_response.total = [valuated, reinsured, approved, claimed]

        # if not claimed and approved - do not set 'total'
        if imis_claim.status == 16 and approved is not None:
            if (fhir_claim_response.total) is not list:
                fhir_claim_response.total = [claimed, approved]
            else:
                fhir_claim_response.total.append(claimed)
                fhir_claim_response.total.append(approved)
        if imis_claim.status == 16 and approved is None:
            if (fhir_claim_response.total) is not list:
                fhir_claim_response.total = [claimed]
            else:
                fhir_claim_response.total.append(claimed)

    @classmethod
    def build_fhir_total_valuated(cls, imis_claim):
        fhir_total = ClaimResponseTotal.construct()
        money = Money.construct()
        fhir_total.amount = money

        if imis_claim.valuated is not None:

            fhir_total.category = CodeableConcept.construct()
            coding = Coding.construct()
            coding.code = "V"
            coding.system = "http://terminology.hl7.org/CodeSystem/adjudication.html"
            coding.display = "Valuated"
            if fhir_total.category.coding is not list:
                fhir_total.category.coding = [coding]
            else:
                fhir_total.category.coding.append(coding)
            fhir_total.category.text = "Valuated < Reinsured < Approved < Claimed"
            fhir_total.amount.value = imis_claim.valuated
            if hasattr(core, 'currency'):
                fhir_total.amount.currency = core.currency

        return fhir_total

    @classmethod
    def build_fhir_total_reinsured(cls, imis_claim):
        fhir_total = ClaimResponseTotal.construct()
        money = Money.construct()
        fhir_total.amount = money

        if imis_claim.reinsured is not None:
            fhir_total.category = CodeableConcept.construct()
            coding = Coding.construct()
            coding.code = "R"
            coding.system = "http://terminology.hl7.org/CodeSystem/adjudication.html"
            coding.display = "Reinsured"
            if fhir_total.category.coding is not list:
                fhir_total.category.coding = [coding]
            else:
                fhir_total.category.coding.append(coding)
            fhir_total.category.text = "Valuated < Reinsured < Approved < Claimed"

            fhir_total.amount.value = imis_claim.reinsured
            if hasattr(core, 'currency'):
                fhir_total.amount.currency = core.currency

        return fhir_total

    @classmethod
    def build_fhir_total_approved(cls, imis_claim):
        fhir_total = ClaimResponseTotal.construct()
        money = Money.construct()
        fhir_total.amount = money

        if imis_claim.approved is not None:

            fhir_total.category = CodeableConcept.construct()
            coding = Coding.construct()
            coding.code = "benefit"
            coding.system = "http://terminology.hl7.org/CodeSystem/adjudication.html"
            coding.display = "Benefit Amount"
            if fhir_total.category.coding is not list:
                fhir_total.category.coding = [coding]
            else:
                fhir_total.category.coding.append(coding)
            fhir_total.category.text = "Approved"

            fhir_total.amount.value = imis_claim.approved
            if hasattr(core, 'currency'):
                fhir_total.amount.currency = core.currency

        return fhir_total

    @classmethod
    def build_fhir_total_claimed(cls, imis_claim):
        fhir_total = ClaimResponseTotal.construct()
        money = Money.construct()
        fhir_total.amount = money

        if imis_claim.claimed is not None:

            fhir_total.category = CodeableConcept.construct()
            coding = Coding.construct()
            coding.code = "submitted"
            coding.system = "http://terminology.hl7.org/CodeSystem/adjudication.html"
            coding.display = "Submitted Amount"
            if fhir_total.category.coding is not list:
                fhir_total.category.coding = [coding]
            else:
                fhir_total.category.coding.append(coding)
            fhir_total.category.text = "Claimed"

            fhir_total.amount.value = imis_claim.claimed
            if hasattr(core, 'currency'):
                fhir_total.amount.currency = core.currency

        return fhir_total

    @classmethod
    def build_fhir_communication_request_reference(cls, fhir_claim_response, imis_claim, reference_type):
        try:
            if imis_claim.feedback is not None:
                request = CommunicationRequestConverter\
                    .build_fhir_resource_reference(imis_claim.feedback, reference_type=reference_type)
                fhir_claim_response.communicationRequest = [request]
        except Feedback.DoesNotExist:
            pass

    @classmethod
    def build_imis_communication_request_reference(cls, imis_claim, fhir_claim_response):
        try:
            if fhir_claim_response.communicationRequest:
                request = fhir_claim_response.communicationRequest[0]
                _, feedback_id = request.reference.split("/")
                imis_claim.feedback = Feedback.objects.get(uuid=feedback_id)
        except Feedback.DoesNotExist:
            pass

    @classmethod
    def build_fhir_type(cls, fhir_claim_response, imis_claim):
        if imis_claim.visit_type:
            fhir_claim_response.type = cls.build_simple_codeable_concept(imis_claim.visit_type)

    @classmethod
    def build_imis_type(cls, imis_claim, fhir_claim_response):
        if fhir_claim_response.type:
            visit_type = fhir_claim_response.type.text
            imis_claim.visit_type = visit_type

    _REVIEW_STATUS_DISPLAY = {
        1: "Idle",
        2: "Not Selected",
        4: "Selected for Review",
        8: "Reviewed",
        16: "ByPassed"
    }

    @classmethod
    def build_fhir_status(cls, fhir_claim_response, imis_claim):
        fhir_claim_response["status"] = cls._REVIEW_STATUS_DISPLAY[imis_claim.review_status]

    @classmethod
    def build_imis_status(cls, imis_claim, fhir_claim_response):
        fhir_status_display = fhir_claim_response.status
        for status_code, status_display in cls._REVIEW_STATUS_DISPLAY.items():
            if fhir_status_display == status_display:
                imis_claim.review_status = status_code
                break

    @classmethod
    def build_fhir_use(cls, fhir_claim_response):
        fhir_claim_response["use"] = "claim"

    @classmethod
    def build_fhir_insurer(cls, fhir_claim_response, imis_claim):
        fhir_claim_response.insurer = Reference.construct()
        fhir_claim_response.insurer.reference = "Organization/" + R4ClaimConfig.get_fhir_claim_organization_code()

    @classmethod
    def build_fhir_items(cls, fhir_claim_response, imis_claim, reference_type):
        for claim_item in cls.generate_fhir_claim_items(imis_claim, reference_type):
            type = claim_item.category.text
            code = claim_item.productOrService.text

            if type == R4ClaimConfig.get_fhir_claim_item_code():
                serviced = cls.get_imis_claim_item_by_code(code, imis_claim.id)
            elif type == R4ClaimConfig.get_fhir_claim_service_code():
                serviced = cls.get_imis_claim_service_by_code(code, imis_claim.id)
            else:
                raise FHIRRequestProcessException(['Could not assign category {} for claim_item: {}'
                                                  .format(type, claim_item)])

            cls._build_response_items(fhir_claim_response, claim_item, serviced, type,
                                      serviced.rejection_reason, imis_claim, reference_type)

    @classmethod
    def build_imis_items(cls, imis_claim: Claim, fhir_claim_response: ClaimResponse):
        # Added new attributes since items shouldn't be saved during mapping to imis
        imis_claim.claim_items = []
        imis_claim.claim_services = []
        for item in fhir_claim_response.item:
            cls._build_imis_claim_item(imis_claim, fhir_claim_response, item)  # same for item and service

    @classmethod
    def _build_response_items(cls, fhir_claim_response, claim_item, imis_service,
                              type, rejected_reason, imis_claim, reference_type):
        cls.build_fhir_item(fhir_claim_response, claim_item, imis_service,
                            type, rejected_reason, imis_claim, reference_type)

    @classmethod
    def generate_fhir_claim_items(cls, imis_claim, reference_type):
        # need to add this three obligatory field to avoid further validation errors
        fhir_claim = {}
        fhir_claim['created'] = imis_claim.date_claimed.isoformat()
        ClaimConverter.build_fhir_status(fhir_claim)
        ClaimConverter.build_fhir_use(fhir_claim)
        claim = FHIRClaim(**fhir_claim)
        ClaimConverter.build_fhir_items(claim, imis_claim, reference_type)
        return claim.item

    @classmethod
    def get_imis_claim_item_by_code(cls, code, imis_claim_id):
        item_code_qs = Item.objects.filter(code=code)
        result = ClaimItem.objects.filter(item_id__in=Subquery(item_code_qs.values('id')), claim_id=imis_claim_id)
        return result[0] if len(result) > 0 else None

    @classmethod
    def _build_imis_claim_item(cls, imis_claim, fhir_claim_response: ClaimResponse, item: ClaimResponseItem):
        extension = item.extension[0]
        _, resource_id = extension.valueReference.reference.split("/")

        if extension.url == 'Medication':
            imis_item = Item.objects.get(uuid=resource_id)
            claim_item = ClaimItem.objects.get(claim=imis_claim, item=imis_item)
        elif extension.url == 'ActivityDefinition':
            imis_service = Service.objects.get(uuid=resource_id)
            claim_item = ClaimService.objects.get(claim=imis_claim, service=imis_service)
        else:
            raise FHIRRequestProcessException(F"Unknnown serviced item type: {extension.url}")

        for next_adjudication in item.adjudication:
            cls.adjudication_to_item(next_adjudication, claim_item, fhir_claim_response)

        if isinstance(claim_item, ClaimItem):
            if imis_claim.claim_items is not list:
                imis_claim.claim_items = [claim_item]
            else:
                imis_claim.claim_items.append(claim_item)
        elif isinstance(claim_item, ClaimService):
            if imis_claim.claim_services is not list:
                imis_claim.claim_services = [claim_item]
            else:
                imis_claim.claim_services.append(claim_item)

    @classmethod
    def _build_imis_claim_service(cls, item: ClaimItem, imis_claim):
        pass

    @classmethod
    def get_imis_claim_service_by_code(cls, code, imis_claim_id):
        service_code_qs = Service.objects.filter(code=code)
        result = ClaimService.objects.filter(service_id__in=Subquery(service_code_qs.values('id')),
                                             claim_id=imis_claim_id)
        return result[0] if len(result) > 0 else None

    @classmethod
    def build_fhir_item(cls, fhir_claim_response, claim_item, item, type, rejected_reason, imis_claim, reference_type):
        claim_response_item = ClaimResponseItem.construct()
        claim_response_item.itemSequence = claim_item.sequence

        adjudication = cls.build_fhir_item_adjudication(item, rejected_reason, imis_claim)
        claim_response_item.adjudication = adjudication

        if type == "item":
            service_type = "Medication"
            serviced_item = item.item
        elif type == "service":
            service_type = "ActivityDefinition"
            serviced_item = item.service
        else:
            raise FHIRRequestProcessException(F"Unknown type of serviced product: {type}")

        serviced_extension = cls.build_serviced_extension(serviced_item, service_type, reference_type)

        if claim_response_item.extension is not list:
            claim_response_item.extension = [serviced_extension]
        else:
            claim_response_item.extension.append(serviced_extension)

        note = cls.build_process_note(fhir_claim_response, item.price_origin)
        if note:
            claim_response_item.noteNumber = [note.number]
        if fhir_claim_response.item is not list:
            fhir_claim_response.item = [claim_response_item]
        else:
            fhir_claim_response.item.append(claim_response_item)

    @classmethod
    def build_serviced_extension(cls, serviced, service_type, reference_type):
        reference = Reference.construct()
        extension = Extension.construct()
        extension.valueReference = reference
        extension.url = service_type
        extension.valueReference = MedicationConverter\
            .build_fhir_resource_reference(serviced, service_type, reference_type=reference_type)
        return extension

    @classmethod
    def __build_item_price(cls, item_price):
        price = Money.construct()
        if hasattr(core,'currency'):
            price.currency = core.currency
        price.value = item_price
        return price

    @classmethod
    def __build_adjudication(cls, item, rejected_reason, amount, category, quantity, explicit_amount=False):
        adjudication = ClaimResponseItemAdjudication.construct()
        adjudication.reason = cls.build_fhir_adjudication_reason(item, rejected_reason)
        if explicit_amount or (amount.value is not None and amount.value != 0.0):
            adjudication.amount = amount
        adjudication.category = category
        adjudication.value = quantity
        return adjudication

    _CLAIM_STATUS_DISPLAY = {
        1: "rejected",
        2: "entered",
        4: "checked",
        8: "processed",
        16: "valuated"
    }

    @classmethod
    def build_fhir_item_adjudication(cls, item, rejected_reason, imis_claim):
        def build_asked_adjudication(status, price):
            category = cls.build_codeable_concept(status, text=cls._CLAIM_STATUS_DISPLAY[status])
            adjudication = cls.__build_adjudication(item, rejected_reason, price, category, item.qty_provided, True)
            return adjudication

        def build_processed_adjudication(status, price):
            category = cls.build_codeable_concept(status, text=cls._CLAIM_STATUS_DISPLAY[status])
            if item.qty_approved is not None and item.qty_approved != 0.0:
                quantity = item.qty_approved
            else:
                quantity = item.qty_provided
            adjudication = cls.__build_adjudication(item, rejected_reason, price, category, quantity)
            return adjudication

        price_asked = cls.__build_item_price(item.price_asked)
        adjudications = []

        if rejected_reason == 0 and imis_claim.status != 1:
            if imis_claim.status >= 2:
                adjudications.append(build_asked_adjudication(2, price_asked))

            if imis_claim.status >= 4:
                price_approved = cls.__build_item_price(item.price_approved)
                adjudications.append(build_processed_adjudication(4, price_approved))

            if imis_claim.status >= 8:
                price_adjusted = cls.__build_item_price(item.price_adjusted)
                adjudications.append(build_processed_adjudication(8, price_adjusted))

            if imis_claim.status == 16:
                price_valuated = cls.__build_item_price(item.price_valuated)
                adjudications.append(build_processed_adjudication(16, price_valuated))
        else:
            adjudications.append(build_asked_adjudication(1, price_asked))

        return adjudications

    @classmethod
    def build_fhir_adjudication_reason(cls, item, rejected_reason):
        text = None
        code = None
        if item.justification is not None:
            text = item.justification
        if not rejected_reason:
            code = "0"
        else:
            code = rejected_reason

        return cls.build_codeable_concept(code, text=text)

    @classmethod
    def adjudication_to_item(cls, adjudication, claim_item, fhir_claim_response):
        status = int(adjudication.category.coding[0].code)
        if status == 1:
            cls.build_item_rejection(claim_item, adjudication)
        if status == 2:
            cls.build_item_entered(claim_item, adjudication)
        if status == 4:
            cls.build_item_checked(claim_item, adjudication)
        if status == 8:
            cls.build_item_processed(claim_item, adjudication)
        if status == 16:
            cls.build_item_valuated(claim_item, adjudication)
        claim_item.status = status
        return claim_item

    @classmethod
    def build_item_rejection(cls, claim_item, adjudication):
        claim_item.rejection_reason = int(adjudication.reason.coding[0].code)
        cls.build_item_entered(claim_item, adjudication)

    @classmethod
    def build_item_entered(cls, claim_item, adjudication):
        claim_item.qty_provided = adjudication.value
        claim_item.price_asked = adjudication.amount.value

    @classmethod
    def build_item_checked(cls, claim_item, adjudication):
        if adjudication.value and adjudication.value != claim_item.qty_provided:
            claim_item.qty_approved = adjudication.value
        if adjudication.amount and adjudication.amount.value != claim_item.price_asked:
            claim_item.price_approved = adjudication.amount.value

    @classmethod
    def build_item_processed(cls, claim_item, adjudication):
        if adjudication.value and adjudication.value != claim_item.qty_provided:
            claim_item.qty_approved = adjudication.value
        if adjudication.amount and adjudication.amount.value != claim_item.price_asked:
            claim_item.price_adjusted = adjudication.amount.value

    @classmethod
    def build_item_valuated(cls, claim_item, adjudication):
        if adjudication.value and adjudication.value != claim_item.qty_provided:
            claim_item.qty_approved = adjudication.value
        if adjudication.amount and adjudication.amount.value != claim_item.price_asked * claim_item.qty_provided:
            claim_item.price_valuated = adjudication.amount.value

    @classmethod
    def build_process_note(cls, fhir_claim_response, string_value):
        result = None
        if string_value:
            note = ClaimResponseProcessNote.construct()
            note.number = FhirUtils.get_next_array_sequential_id(fhir_claim_response.processNote)
            note.text = string_value
            if fhir_claim_response.processNote is not list:
                fhir_claim_response.processNote = [note]
            else:
                fhir_claim_response.processNote.append(note)
            result = note
        return result

    @classmethod
    def build_fhir_requestor(cls, fhir_claim_response, imis_claim, reference_type):
        if imis_claim.health_facility is not None:
            fhir_claim_response.requestor = HealthcareServiceConverter\
                .build_fhir_resource_reference(imis_claim.health_facility, reference_type=reference_type)

    @classmethod
    def build_imis_requestor(cls, imis_claim, fhir_claim_response):
        if fhir_claim_response.requestor is not None:
            requestor = fhir_claim_response.requestor
            _, hf_id = requestor.reference.split("/")
            imis_claim.health_facility = HealthFacility.objects.get(uuid=hf_id)

    @classmethod
    def build_fhir_billable_period(cls, fhir_claim_response, imis_claim):
        extension = Extension.construct()
        extension.url = "billablePeriod"
        extension.valuePeriod = Period.construct()
        if imis_claim.date_from:
            extension.valuePeriod.start = imis_claim.date_from.isoformat()
        if imis_claim.date_to:
            extension.valuePeriod.end = imis_claim.date_to.isoformat()
        if fhir_claim_response.extension is not list:
            fhir_claim_response.extension = [extension]
        else:
            fhir_claim_response.extension.append(extension)

    @classmethod
    def build_imis_billable_period(cls, imis_claim, fhir_claim_response):
        billable_period = next(filter(lambda x: x.url == 'billablePeriod', fhir_claim_response.extension))
        iso_start_date = billable_period.valuePeriod.start
        iso_end_date = billable_period.valuePeriod.end
        if iso_start_date:
            imis_claim.date_from = datetime.date.fromisoformat(iso_start_date)
        if iso_end_date:
            imis_claim.date_to = datetime.date.fromisoformat(iso_end_date)

    @classmethod
    def build_fhir_diagnoses(cls, fhir_claim_response, imis_claim, reference_type):
        diagnoses = fhir_claim_response.extension
        cls.build_fhir_diagnosis(diagnoses, imis_claim.icd, ImisClaimIcdTypes.ICD_0.value, reference_type)
        if imis_claim.icd_1:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_1, ImisClaimIcdTypes.ICD_1.value, reference_type)
        if imis_claim.icd_2:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_2, ImisClaimIcdTypes.ICD_2.value, reference_type)
        if imis_claim.icd_3:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_3, ImisClaimIcdTypes.ICD_3.value, reference_type)
        if imis_claim.icd_4:
            cls.build_fhir_diagnosis(diagnoses, imis_claim.icd_4, ImisClaimIcdTypes.ICD_4.value, reference_type)

    @classmethod
    def build_imis_diagnoses(cls, imis_claim, fhir_claim_response):
        def get_diagnosis_from_extension(icd_order):
            return next(filter(lambda x: x.url == icd_order, fhir_claim_response.extension), None)

        def get_diagnosis_by_code(ext_obj):
            _, code = ext_obj.valueReference.reference.split("/")
            return Diagnosis.objects.get(code=code, validity_to=None)

        def assign_diagnosis_from_ext(fhir_icd: str, imis_icd_attr: str):
            icd_ext = get_diagnosis_from_extension(fhir_icd)
            diagnosis = get_diagnosis_by_code(icd_ext) if icd_ext else None
            setattr(imis_claim, imis_icd_attr, diagnosis)

        assign_diagnosis_from_ext(ImisClaimIcdTypes.ICD_0.value, 'icd')
        assign_diagnosis_from_ext(ImisClaimIcdTypes.ICD_1.value, 'icd_1')
        assign_diagnosis_from_ext(ImisClaimIcdTypes.ICD_2.value, 'icd_2')
        assign_diagnosis_from_ext(ImisClaimIcdTypes.ICD_3.value, 'icd_3')
        assign_diagnosis_from_ext(ImisClaimIcdTypes.ICD_4.value, 'icd_4')

    @classmethod
    def build_fhir_diagnosis(cls, diagnoses, icd_code, icd_type, reference_type):
        extension = Extension.construct()
        extension.url = icd_type
        extension.valueReference = ConditionConverter\
            .build_fhir_resource_reference(icd_code, reference_type=reference_type)

        if type(diagnoses) is not list:
            diagnoses = [extension]
        else:
            diagnoses.append(extension)

    @classmethod
    def build_fhir_adjustment(cls, fhir_claim_response, imis_claim):
        fhir_payment = ClaimResponsePayment.construct()
        fhir_payment.adjustmentReason = ClaimResponseConverter.build_simple_codeable_concept(imis_claim.adjustment)
        fhir_claim_response.payment = fhir_payment

    @classmethod
    def build_imis_adjustment(cls, imis_claim, fhir_claim_response):
        if fhir_claim_response.payment:
            adjustment = fhir_claim_response.payment.adjustmentReason.text
            imis_claim.adjustment = adjustment
