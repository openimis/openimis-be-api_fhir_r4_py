from api_fhir_r4.configurations import GeneralConfiguration, R4CommunicationRequestConfig as Config
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.utils import DbManagerUtils
from claim.models import Claim, Feedback
from insuree.models import Insuree
from django.utils.translation import gettext as _
from fhir.resources.communication import Communication, CommunicationPayload
from fhir.resources.extension import Extension


class CommunicationConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_feedback, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_communication = {}
        cls.build_fhir_status(fhir_communication)
        fhir_communication = Communication(**fhir_communication)
        cls.build_fhir_identifiers(fhir_communication, imis_feedback)
        cls.build_fhir_subject(fhir_communication, imis_feedback, reference_type)
        cls.build_fhir_about(fhir_communication, imis_feedback, reference_type)
        cls.build_fhir_payloads(fhir_communication, imis_feedback)
        return fhir_communication

    @classmethod
    def to_imis_obj(cls, fhir_communication, audit_user_id):
        errors = []
        fhir_communication = Communication(**fhir_communication)
        cls._validate_fhir_status(fhir_communication)
        cls._validate_fhir_subject(fhir_communication)
        cls._validate_fhir_about(fhir_communication)
        cls._validate_fhir_payload(fhir_communication)
        imis_feedback = Feedback()
        cls.build_imis_about(imis_feedback, fhir_communication, errors)
        cls.build_imis_payloads(imis_feedback, fhir_communication, errors)
        imis_feedback.audit_user_id = audit_user_id
        return imis_feedback

    @classmethod
    def build_fhir_identifiers(cls, fhir_communication, imis_feedback):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_feedback)
        fhir_communication.identifier = identifiers
        return fhir_communication

    @classmethod
    def build_all_identifiers(cls, identifiers, imis_object):
        # Feedback does not provide code reference
        cls.build_fhir_uuid_identifier(identifiers, imis_object)

    @classmethod
    def build_fhir_payloads(cls, fhir_communication, imis_feedback):
        fhir_communication.payload = []
        cls.build_fhir_payload(
            fhir_communication.payload,
            Config.get_fhir_care_rendered_code(),
            "yes" if imis_feedback.care_rendered is True else "no"
        )
        cls.build_fhir_payload(
            fhir_communication.payload,
            Config.get_fhir_payment_asked_code(),
            "yes" if imis_feedback.payment_asked is True else "no"
        )
        cls.build_fhir_payload(
            fhir_communication.payload,
            Config.get_fhir_drug_prescribed_code(),
            "yes" if imis_feedback.drug_prescribed is True else "no"
        )
        cls.build_fhir_payload(
            fhir_communication.payload,
            Config.get_fhir_drug_received_code(),
            "yes" if imis_feedback.drug_received is True else "no"
        )
        cls.build_fhir_payload(
            fhir_communication.payload,
            Config.get_fhir_asessment_code(),
            imis_feedback.asessment
        )

    @classmethod
    def build_fhir_payload(cls, fhir_payload, code, content_string):
        payload = {}
        payload['contentString'] = content_string
        payload = CommunicationPayload(**payload)
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
    def build_fhir_status(cls, fhir_communication):
        fhir_communication['status'] = "completed"

    @classmethod
    def build_fhir_subject(cls, fhir_communication, imis_feedback, reference_type):
        fhir_communication.subject = cls.build_fhir_resource_reference(
            imis_feedback.claim.insuree,
            reference_type=reference_type,
            type="Patient",
            display=imis_feedback.claim.insuree.chf_id
        )

    @classmethod
    def build_fhir_about(cls, fhir_communication, imis_feedback, reference_type):
        fhir_communication.about = []
        reference = cls.build_fhir_resource_reference(
            imis_feedback.claim,
            reference_type=reference_type,
            type="Claim",
            display=imis_feedback.claim.code
        )
        fhir_communication.about.append(reference)

    @classmethod
    def build_imis_about(cls, imis_feedback, fhir_communication, errors):
        claim_uuid = cls.__get_claim_reference(fhir_communication.about[0].reference)
        try:
            imis_feedback.claim = Claim.objects.get(uuid=claim_uuid, validity_to__isnull=True)
        except Exception:
            raise FHIRException(
                _('Claim does not exist')
            )

    @classmethod
    def __get_claim_reference(cls, claim):
        return claim.rsplit('/', 1)[1]

    @classmethod
    def build_imis_payloads(cls, imis_feedback, fhir_communication, errors):
        payloads = fhir_communication.payload
        for payload in payloads:
            code = cls.get_code_from_extension_codeable_concept(payload.extension[0])
            fhir_content_string = payload.contentString
            if code == Config.get_fhir_care_rendered_code():
                cls.build_imis_care_rendered(imis_feedback, fhir_content_string)
            if code == Config.get_fhir_payment_asked_code():
                cls.build_imis_payment_asked(imis_feedback, fhir_content_string)
            if code == Config.get_fhir_drug_prescribed_code():
                cls.build_imis_drug_prescribed(imis_feedback, fhir_content_string)
            if code == Config.get_fhir_drug_received_code():
                cls.build_imis_drug_received(imis_feedback, fhir_content_string)
            if code == Config.get_fhir_asessment_code():
                cls.build_imis_asessment(imis_feedback, fhir_content_string)

    @classmethod
    def build_imis_care_rendered(cls, imis_feedback, fhir_content_string):
        value = cls._convert_bool_value(fhir_content_string)
        if value:
            imis_feedback.care_rendered = value

    @classmethod
    def build_imis_payment_asked(cls, imis_feedback, fhir_content_string):
        value = cls._convert_bool_value(fhir_content_string)
        if value:
            imis_feedback.payment_asked = value

    @classmethod
    def build_imis_drug_prescribed(cls, imis_feedback, fhir_content_string):
        value = cls._convert_bool_value(fhir_content_string)
        if value:
            imis_feedback.drug_prescribed = value

    @classmethod
    def build_imis_drug_received(cls, imis_feedback, fhir_content_string):
        value = cls._convert_bool_value(fhir_content_string)
        if value:
            imis_feedback.drug_received = value

    @classmethod
    def build_imis_asessment(cls, imis_feedback, fhir_content_string):
        imis_feedback.asessment = fhir_content_string

    @classmethod
    def _convert_bool_value(cls, fhir_content_string):
        if fhir_content_string == "yes":
            return True
        if fhir_content_string == "no":
            return False
        return None

    @classmethod
    def get_reference_obj_id(cls, imis_feedback):
        return imis_feedback.uuid

    @classmethod
    def get_fhir_resource_type(cls):
        return Communication

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_feedback_id = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Feedback, pk=imis_feedback_id)

    @classmethod
    def get_reference_obj_uuid(cls, imis_feedback):
        return imis_feedback.uuid

    @classmethod
    def _validate_fhir_about(cls, fhir_communication):
        if not fhir_communication.about:
            raise FHIRException(
                _('about is required')
            )

    @classmethod
    def _validate_fhir_subject(cls, fhir_communication):
        if not fhir_communication.subject:
            raise FHIRException(
                _('subject is required')
            )
        else:
            patient_uuid = fhir_communication.subject.reference.rsplit('/', 1)[1]
            if Insuree.objects.filter(uuid=patient_uuid, validity_to__isnull=True).count() == 0:
                raise FHIRException(
                    _('Patient does not exist')
                )

    @classmethod
    def _validate_fhir_status(cls, fhir_communication):
        if not fhir_communication.status:
            raise FHIRException(
                _('status is required field')
            )
        else:
            if not fhir_communication.status == 'completed':
                raise FHIRException(
                    _('status value must be = completed')
                )

    @classmethod
    def _validate_fhir_payload(cls, fhir_communication):
        if not fhir_communication.payload:
            raise FHIRException(
                _('payload is required')
            )
        else:
            if len(fhir_communication.payload) != 5:
                raise FHIRException(
                    _('payload must have 5 elements')
                )
            else:
                required_payload = [
                    'CareRendered', 'PaymentAsked',
                    'DrugPrescribed', 'DrugReceived', 'Asessment'
                ]
                extension_values = []
                for payload in fhir_communication.payload:
                    extension_values.append(
                        cls.get_code_from_extension_codeable_concept(payload.extension[0])
                    )
                required_payload.sort()
                extension_values.sort()
                if required_payload != extension_values:
                    raise FHIRException(
                        _(F"payload must support all five elemets:"
                          " 'CareRendered', 'PaymentAsked',"
                          " 'DrugPrescribed', 'DrugReceived', 'Asessment'")
                    )
