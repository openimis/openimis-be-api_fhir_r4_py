from claim.models import Feedback, ClaimItem, ClaimService, Claim, ClaimAdmin
from django.db.models import Subquery
from medical.models import Item, Service
import core

from api_fhir_r4.configurations import GeneralConfiguration, R4ClaimConfig
from api_fhir_r4.converters import BaseFHIRConverter, CommunicationRequestConverter, ReferenceConverterMixin
from api_fhir_r4.converters.claimConverter import ClaimConverter
from api_fhir_r4.converters.patientConverter import PatientConverter
from api_fhir_r4.converters.claimAdminPractitionerConverter import ClaimAdminPractitionerConverter
from api_fhir_r4.converters.medicationConverter import MedicationConverter
from api_fhir_r4.exceptions import FHIRRequestProcessException
from api_fhir_r4.mapping.claimMapping import ClaimResponseMapping
from api_fhir_r4.models import ClaimResponseV2 as ClaimResponse
from fhir.resources.money import Money
from fhir.resources.claimresponse import ClaimResponseItem, ClaimResponseItemAdjudication, \
    ClaimResponseProcessNote, ClaimResponseTotal
from fhir.resources.reference import Reference
from fhir.resources.extension import Extension
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
        cls.build_fhir_pk(fhir_claim_response, imis_claim, reference_type)
        ClaimConverter.build_fhir_identifiers(fhir_claim_response, imis_claim)
        cls.build_fhir_items(fhir_claim_response, imis_claim, reference_type)
        cls.build_patient_reference(fhir_claim_response, imis_claim, reference_type)
        cls.build_fhir_total_list(fhir_claim_response, imis_claim)
        cls.build_fhir_communication_request_reference(fhir_claim_response, imis_claim, reference_type)
        cls.build_fhir_type(fhir_claim_response, imis_claim)
        cls.build_fhir_insurer(fhir_claim_response)
        cls.build_fhir_requestor(fhir_claim_response, imis_claim, reference_type)
        cls.build_fhir_request(fhir_claim_response, imis_claim, reference_type)
        return fhir_claim_response
               
    @classmethod
    def to_imis_obj(cls, fhir_claim_response, audit_user_id):
        errors = []
        fhir_claim_response = ClaimResponse(**fhir_claim_response)
        imis_claim = cls.get_imis_claim_from_response(fhir_claim_response)
        cls.build_imis_outcome(imis_claim, fhir_claim_response)
        cls.build_imis_items(imis_claim, fhir_claim_response)
        cls.build_imis_communication_request_reference(imis_claim, fhir_claim_response)
        cls.build_imis_type(imis_claim, fhir_claim_response)
        cls.build_imis_status(imis_claim, fhir_claim_response)
        cls.build_imis_requestor(imis_claim, fhir_claim_response)
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
        status = imis_claim.status
        outcome = ClaimResponseMapping.claim_outcome[f'{status}']
        fhir_claim_response["outcome"] = outcome

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

    @classmethod
    def get_status_code_by_display(cls, claim_response_display):
        for code, display in ClaimResponseMapping.claim_outcome.items():
            if display == claim_response_display:
                return code
        return None

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
    def build_fhir_total_list(cls, fhir_claim_response, imis_claim):
        total_claimed = 0
        total_approved = 0
        total_adjusted = 0
        total_rejected = 0
        total_valuated = 0
        if fhir_claim_response:
            items = fhir_claim_response.item
            for item in items:
                for adjudication in item.adjudication:
                    rejection_reason = adjudication.reason.coding[0].code
                    if rejection_reason == '0':
                        if adjudication.category.coding[0].code == str(Claim.STATUS_ENTERED):
                            total_claimed += adjudication.amount.value*adjudication.value
                        if adjudication.category.coding[0].code == str(Claim.STATUS_PROCESSED):
                            total_adjusted += adjudication.amount.value*adjudication.value
                        if adjudication.category.coding[0].code == str(Claim.STATUS_CHECKED):
                            total_approved += adjudication.amount.value*adjudication.value
                        if adjudication.category.coding[0].code == str(Claim.STATUS_VALUATED):
                            total_valuated += adjudication.amount.value*adjudication.value
                    else:
                        total_claimed += adjudication.amount.value*adjudication.value

        fhir_total = []
        if imis_claim.status >= Claim.STATUS_ENTERED:
            fhir_total.append(cls.build_fhir_total(imis_claim, Claim.STATUS_ENTERED, total_claimed))
        if imis_claim.status >= Claim.STATUS_CHECKED:
            fhir_total.append(cls.build_fhir_total(imis_claim, Claim.STATUS_CHECKED, total_approved))
        if imis_claim.status >= Claim.STATUS_PROCESSED:
            fhir_total.append(cls.build_fhir_total(imis_claim, Claim.STATUS_PROCESSED, total_adjusted))
        if imis_claim.status == Claim.STATUS_VALUATED:
            fhir_total.append(cls.build_fhir_total(imis_claim, Claim.STATUS_VALUATED, total_valuated))

        if len(fhir_total) > 0:
            fhir_claim_response.total = fhir_total

    @classmethod
    def build_fhir_total(cls, imis_claim, claim_status, total):
        fhir_total = ClaimResponseTotal.construct()
        money = Money.construct()
        fhir_total.amount = money
        fhir_total.category = cls.build_codeable_concept(
            system=ClaimResponseMapping.claim_status_system,
            code=claim_status,
            display=ClaimResponseMapping.claim_status[f'{claim_status}']
        )
        fhir_total.amount.value = total
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
            fhir_claim_response.type = cls.build_codeable_concept(
                system=ClaimResponseMapping.visit_type_system,
                code=imis_claim.visit_type,
                display=ClaimResponseMapping.visit_type[f'{imis_claim.visit_type}']
            )

    @classmethod
    def build_imis_type(cls, imis_claim, fhir_claim_response):
        if fhir_claim_response.type:
            coding = fhir_claim_response.type.coding
            if coding and len(coding) > 0:
                visit_type = fhir_claim_response.type.coding[0].code
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
        fhir_claim_response["status"] = "active"

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
    def build_fhir_insurer(cls, fhir_claim_response):
        fhir_claim_response.insurer = Reference.construct()
        fhir_claim_response.insurer.reference = "openIMIS"

    @classmethod
    def build_fhir_items(cls, fhir_claim_response, imis_claim, reference_type):
        fhir_claim_response.item = []
        cls.build_fhir_items_for_imis_items(fhir_claim_response, imis_claim, reference_type)
        cls.build_fhir_items_for_imis_services(fhir_claim_response, imis_claim, reference_type)

    @classmethod
    def build_fhir_items_for_imis_services(cls, fhir_claim_response, imis_claim, reference_type):
        for claim_service in imis_claim.services.filter(validity_to=None).all():
            if claim_service:
                item_type = R4ClaimConfig.get_fhir_claim_service_code()
                cls.build_fhir_item(fhir_claim_response, claim_service, item_type, claim_service.rejection_reason, imis_claim, reference_type)

    @classmethod
    def build_fhir_items_for_imis_items(cls, fhir_claim_response, imis_claim, reference_type):
        for claim_item in imis_claim.items.filter(validity_to=None).all():
            if claim_item:
                item_type = R4ClaimConfig.get_fhir_claim_item_code()
                cls.build_fhir_item(fhir_claim_response, claim_item, item_type, claim_item.rejection_reason, imis_claim, reference_type)


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
    def get_imis_claim_item_by_code(cls, code, imis_claim_id):
        item_code_qs = Item.objects.filter(code=code)
        result = ClaimItem.objects.filter(item_id__in=Subquery(item_code_qs.values('id')), claim_id=imis_claim_id)
        return result[0] if len(result) > 0 else None

    @classmethod
    def _build_imis_claim_item(cls, imis_claim, fhir_claim_response: ClaimResponse, item: ClaimResponseItem):
        extension = item.extension[0]
        _, resource_id = extension.valueReference.reference.split("/")

        if extension.valueReference.type == 'Medication':
            imis_item = Item.objects.get(uuid=resource_id)
            claim_item = ClaimItem.objects.get(claim=imis_claim, item=imis_item)
        elif extension.valueReference.type == 'ActivityDefinition':
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
    def build_fhir_item(cls, fhir_claim_response, item, type, rejected_reason, imis_claim, reference_type):
        claim_response_item = ClaimResponseItem.construct()
        claim_response_item.itemSequence = FhirUtils.get_next_array_sequential_id(fhir_claim_response.item)

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

        fhir_claim_response.item.append(claim_response_item)

    @classmethod
    def build_serviced_extension(cls, serviced, service_type, reference_type):
        reference = Reference.construct()
        extension = Extension.construct()
        extension.valueReference = reference
        extension.url = f'{GeneralConfiguration.get_system_base_url()}StructureDefinition/claim-item-reference'
        extension.valueReference = MedicationConverter\
            .build_fhir_resource_reference(serviced, service_type, reference_type=reference_type, display=serviced.code)
        return extension

    @classmethod
    def __build_item_price(cls, item_price):
        price = Money.construct()
        if hasattr(core, 'currency'):
            price.currency = core.currency
        price.value = item_price
        return price

    @classmethod
    def __build_adjudication(cls, item, rejected_reason, amount, category, quantity, explicit_amount=False):
        adjudication = ClaimResponseItemAdjudication.construct()
        adjudication.reason = cls.build_fhir_adjudication_reason(item, rejected_reason)
        adjudication.amount = amount
        adjudication.category = category
        adjudication.value = quantity
        return adjudication

    @classmethod
    def build_fhir_item_adjudication(cls, item, rejected_reason, imis_claim):
        def build_asked_adjudication(status, price):
            category = cls.build_codeable_concept(
                system=ClaimResponseMapping.claim_status_system,
                code=status,
                display=ClaimResponseMapping.claim_status[f'{status}']
            )
            adjudication = cls.__build_adjudication(item, rejected_reason, price, category, item.qty_provided, True)
            return adjudication

        def build_processed_adjudication(status, price):
            category = cls.build_codeable_concept(
                system=ClaimResponseMapping.claim_status_system,
                code=status,
                display=ClaimResponseMapping.claim_status[f'{status}']
            )
            if item.qty_approved is not None and item.qty_approved != 0.0:
                quantity = item.qty_approved
            else:
                quantity = item.qty_provided
            adjudication = cls.__build_adjudication(item, rejected_reason, price, category, quantity)
            return adjudication

        price_asked = cls.__build_item_price(item.price_asked)
        adjudications = []

        if rejected_reason == 0 and imis_claim.status != 1:
            if imis_claim.status >= Claim.STATUS_ENTERED:
                adjudications.append(build_asked_adjudication(Claim.STATUS_ENTERED, price_asked))

            if imis_claim.status >= Claim.STATUS_CHECKED:
                if item.price_approved:
                    price_approved = cls.__build_item_price(item.price_approved)
                    adjudications.append(build_processed_adjudication(Claim.STATUS_CHECKED, price_approved))
                else:
                    adjudications.append(build_processed_adjudication(Claim.STATUS_CHECKED, price_asked))
            if imis_claim.status >= Claim.STATUS_PROCESSED:
                if item.price_adjusted:
                    price_adjusted = cls.__build_item_price(item.price_adjusted)
                    adjudications.append(build_processed_adjudication(Claim.STATUS_PROCESSED, price_adjusted))
                else:
                    adjudications.append(build_processed_adjudication(Claim.STATUS_PROCESSED, price_asked))
            if imis_claim.status == Claim.STATUS_VALUATED:
                if item.price_valuated:
                    price_valuated = cls.__build_item_price(item.price_valuated)
                    adjudications.append(build_processed_adjudication(Claim.STATUS_VALUATED, price_valuated))
                else:
                    adjudications.append(build_processed_adjudication(Claim.STATUS_VALUATED, price_asked))
        else:
            adjudications.append(build_asked_adjudication(1, price_asked))

        return adjudications

    @classmethod
    def build_fhir_adjudication_reason(cls, item, rejected_reason):
        code = "0" if not rejected_reason else rejected_reason
        return cls.build_codeable_concept(
            system=ClaimResponseMapping.rejection_reason_system,
            code=code,
            display=ClaimResponseMapping.rejection_reason[int(code)]
        )

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
            note.text = string_value
            note.number = FhirUtils.get_next_array_sequential_id(fhir_claim_response.processNote)
            if fhir_claim_response.processNote is not list:
                fhir_claim_response.processNote = [note]
            else:
                fhir_claim_response.processNote.append(note)
            result = note
        return result

    @classmethod
    def build_fhir_requestor(cls, fhir_claim_response, imis_claim, reference_type):
        if imis_claim.admin is not None:
            fhir_claim_response.requestor = ClaimAdminPractitionerConverter\
                .build_fhir_resource_reference(imis_claim.admin, reference_type=reference_type)

    @classmethod
    def build_imis_requestor(cls, imis_claim, fhir_claim_response):
        if fhir_claim_response.requestor is not None:
            requestor = fhir_claim_response.requestor
            _, claim_admin_uuid = requestor.reference.split("/")
            imis_claim.admin = ClaimAdmin.objects.get(uuid=claim_admin_uuid)

    @classmethod
    def build_fhir_request(cls, fhir_claim_response: ClaimResponse, imis_claim: Claim, reference_type):
        fhir_claim_response.request = ClaimConverter\
            .build_fhir_resource_reference(imis_claim, reference_type=reference_type)
