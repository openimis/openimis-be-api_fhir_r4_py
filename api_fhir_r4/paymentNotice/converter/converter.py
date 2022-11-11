from .to_fhir_converter import PaymentNoticeToFhirConverter
from .to_imis_converter import PaymentNoticeToImisConverter
from api_fhir_r4.converters import ReferenceConverterMixin


class PaymentNoticeConverter(
    PaymentNoticeToImisConverter, PaymentNoticeToFhirConverter
):

    @classmethod
    def to_imis_obj(cls, fhir_payment_notice, audit_user_id=None):
        return PaymentNoticeToImisConverter.to_imis_obj(fhir_payment_notice)

    @classmethod
    def to_fhir_obj(cls, imis_payment, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        return PaymentNoticeToFhirConverter.to_fhir_obj(imis_payment, reference_type)
