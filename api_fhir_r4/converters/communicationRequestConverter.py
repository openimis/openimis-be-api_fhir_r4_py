from claim.models import Feedback

from api_fhir_r4.configurations import R4CommunicationRequestConfig as Config
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from fhir.resources.communicationrequest import CommunicationRequest
from api_fhir_r4.utils import DbManagerUtils


class CommunicationRequestConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_feedback, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_communication_request = CommunicationRequest.construct()
        fhir_communication_request.status = "unknown"
        cls.build_fhir_occurrence_datetime(fhir_communication_request, imis_feedback)
        cls.build_fhir_pk(fhir_communication_request, imis_feedback, reference_type)
        cls.build_fhir_identifiers(fhir_communication_request, imis_feedback)
        cls.build_fhir_reason_codes(fhir_communication_request, imis_feedback)
        cls.build_fhir_status(fhir_communication_request)
        return fhir_communication_request

    @classmethod
    def get_reference_obj_id(cls, imis_feedback):
        return imis_feedback.uuid

    @classmethod
    def get_fhir_resource_type(cls):
        return CommunicationRequest

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_feedback_id = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Feedback, pk=imis_feedback_id)

    @classmethod
    def build_fhir_occurrence_datetime(cls, fhir_communication_request, imis_feedback):
        feedback_date = imis_feedback.feedback_date
        if feedback_date:
            fhir_communication_request.occurrenceDateTime = feedback_date.isoformat()

    @classmethod
    def build_fhir_identifiers(cls, fhir_communication_request, imis_feedback):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_feedback)
        fhir_communication_request.identifier = identifiers

    @classmethod
    def build_all_identifiers(cls, identifiers, imis_object):
        # Feedback does not provide code reference
        cls.build_fhir_uuid_identifier(identifiers, imis_object)
        cls.build_fhir_id_identifier(identifiers, imis_object)

    @classmethod
    def build_fhir_reason_codes(cls, fhir_communication_request, imis_feedback):
        reasons = [cls.build_codeable_concept(Config.get_fhir_care_rendered_code(),
                                              text=str(imis_feedback.care_rendered)),
                   cls.build_codeable_concept(Config.get_fhir_payment_asked_code(),
                                              text=str(imis_feedback.payment_asked)),
                   cls.build_codeable_concept(Config.get_fhir_drug_prescribed_code(),
                                              text=str(imis_feedback.drug_prescribed)),
                   cls.build_codeable_concept(Config.get_fhir_drug_received_code(),
                                              text=str(imis_feedback.drug_received))]
        if imis_feedback.asessment is not None:
            reasons.append(cls.build_codeable_concept(Config.get_fhir_asessment_code(),
                                                      text=str(imis_feedback.asessment)))
        fhir_communication_request.reasonCode = reasons

    @classmethod
    def build_fhir_status(cls, fhir_claim_response):
        fhir_claim_response.status = "active"
