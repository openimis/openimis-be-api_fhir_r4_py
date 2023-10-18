from api_fhir_r4.configurations import GeneralConfiguration, \
    R4CommunicationRequestConfig as Config
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.mapping.feedbackMapping import FeedbackStatus
from api_fhir_r4.utils import DbManagerUtils
from claim.models import Claim
from fhir.resources.R4B.communicationrequest import CommunicationRequest, CommunicationRequestPayload
from fhir.resources.R4B.extension import Extension


class CommunicationRequestConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_claim, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_communication_request = CommunicationRequest.construct()
        fhir_communication_request.status = "active"
        cls.build_fhir_status(fhir_communication_request, imis_claim)
        cls.build_fhir_status_reason(fhir_communication_request, imis_claim)
        cls.build_fhir_subject(fhir_communication_request, imis_claim, reference_type)
        cls.build_fhir_about(fhir_communication_request, imis_claim, reference_type)
        cls.build_fhir_recipient(fhir_communication_request, imis_claim, reference_type)
        cls.build_fhir_payloads(fhir_communication_request)
        return fhir_communication_request

    @classmethod
    def get_reference_obj_id(cls, imis_claim):
        return imis_claim.uuid

    @classmethod
    def get_reference_obj_code(cls, imis_claim):
        return imis_claim.code

    @classmethod
    def get_fhir_resource_type(cls):
        return CommunicationRequest

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        return DbManagerUtils.get_object_or_none(
            Claim,
            **cls.get_database_query_id_parameteres_from_reference(reference))


    @classmethod
    def get_reference_obj_uuid(cls, imis_claim):
        return imis_claim.uuid

    @classmethod
    def build_fhir_payloads(cls, fhir_communication_request):
        fhir_communication_request.payload = []
        cls.build_fhir_payload(
            fhir_communication_request.payload,
            Config.get_fhir_care_rendered_code(),
            "Care Rendered? (yes|no)"
        )
        cls.build_fhir_payload(
            fhir_communication_request.payload,
            Config.get_fhir_payment_asked_code(),
            "Payment Asked? (yes|no)"
        )
        cls.build_fhir_payload(
            fhir_communication_request.payload,
            Config.get_fhir_drug_prescribed_code(),
            "Drug Prescribed? (yes|no)"
        )
        cls.build_fhir_payload(
            fhir_communication_request.payload,
            Config.get_fhir_drug_received_code(),
            "Drug Received? (yes|no)"
        )
        cls.build_fhir_payload(
            fhir_communication_request.payload,
            Config.get_fhir_asessment_code(),
            "Asessment? (0|1|2|3|4|5)"
        )

    @classmethod
    def build_fhir_payload(cls, fhir_payload, code, content_string):
        payload = {}
        payload['contentString'] = content_string
        payload = CommunicationRequestPayload(**payload)
        payload.extension = []

        extension = Extension.construct()
        url = f'{GeneralConfiguration.get_system_base_url()}StructureDefinition/communication-payload-type'
        system = f'{GeneralConfiguration.get_system_base_url()}CodeSystem/feedback-payload'
        extension.url = url
        extension.valueCodeableConcept = cls.build_codeable_concept(
            system=system,
            code=code
        )
        payload.extension.append(extension)

        fhir_payload.append(payload)

    @classmethod
    def build_fhir_status(cls, fhir_communication_request, imis_claim):
        feedback_code = FeedbackStatus.map_status(imis_claim.feedback_status)
        fhir_communication_request.status = feedback_code

    @classmethod
    def build_fhir_status_reason(cls, fhir_communication_request, imis_claim):
        display = FeedbackStatus.map_code_display(imis_claim.feedback_status)
        system = f'{GeneralConfiguration.get_system_base_url()}CodeSystem/feedback-status'
        fhir_communication_request.statusReason = cls.build_codeable_concept(
            system=system,
            code=imis_claim.feedback_status,
            display=display
        )

    @classmethod
    def build_fhir_subject(cls, fhir_communication_request, imis_claim, reference_type):
        fhir_communication_request.subject = cls.build_fhir_resource_reference(
            imis_claim.insuree,
            reference_type=reference_type,
            type="Patient",
            display=imis_claim.insuree.chf_id
        )

    @classmethod
    def build_fhir_about(cls, fhir_communication_request, imis_claim, reference_type):
        fhir_communication_request.about = []
        reference = cls.build_fhir_resource_reference(
            imis_claim,
            reference_type=reference_type,
            type="Claim",
            display=imis_claim.code
        )
        fhir_communication_request.about.append(reference)

    @classmethod
    def build_fhir_recipient(cls, fhir_communication_request, imis_claim, reference_type):
        fhir_communication_request.recipient = []
        reference = cls.build_fhir_resource_reference(
            imis_claim.admin,
            reference_type=reference_type,
            type="Practitioner",
            display=imis_claim.admin.code
        )
        fhir_communication_request.recipient.append(reference)
