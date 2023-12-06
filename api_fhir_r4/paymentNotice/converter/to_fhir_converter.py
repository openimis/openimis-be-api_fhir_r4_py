from fhir.resources.R4B.reference import Reference
from fhir.resources.R4B.paymentnotice import PaymentNotice

from api_fhir_r4.configurations import (
    R4IdentifierConfig
)
from api_fhir_r4.converters import (
    BaseFHIRConverter,
    ReferenceConverterMixin
)
from api_fhir_r4.defaultConfig import DEFAULT_CFG
from api_fhir_r4.paymentNotice.mapping import (
    PaymentNoticeStatusMapping,
    PaymentNoticePaymentStatusMapping
)


class PaymentNoticeToFhirConverter(BaseFHIRConverter, ReferenceConverterMixin):
    @classmethod
    def to_fhir_obj(cls, imis_payment, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_payment_notice = {}
        cls.build_fhir_status(fhir_payment_notice, imis_payment)
        cls.build_fhir_created(fhir_payment_notice, imis_payment)
        cls.build_fhir_amount(fhir_payment_notice, imis_payment)
        cls.build_fhir_payment(fhir_payment_notice, imis_payment)
        cls.build_fhir_recipient(fhir_payment_notice)
        fhir_payment_notice = PaymentNotice(**fhir_payment_notice)
        cls.build_fhir_pk(fhir_payment_notice, imis_payment, reference_type)
        cls.build_fhir_identifiers(fhir_payment_notice, imis_payment)
        cls.build_fhir_request(fhir_payment_notice, imis_payment, reference_type)
        cls.build_fhir_payment_date(fhir_payment_notice, imis_payment)
        cls.build_fhir_payment_status(fhir_payment_notice, imis_payment)
        return fhir_payment_notice

    @classmethod
    def build_fhir_identifiers(cls, fhir_invoice, imis_invoice):
        identifiers = []
        cls.build_fhir_uuid_identifier(identifiers, imis_invoice)
        fhir_invoice.identifier = identifiers

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

    @classmethod
    def build_fhir_status(cls, fhir_payment_notice, imis_payment):
        imis_invoice = cls._fetch_invoice_related_to_payment(imis_payment)
        fhir_payment_notice['status'] = PaymentNoticeStatusMapping\
            .to_fhir_status[imis_invoice.status]

    @classmethod
    def build_fhir_created(cls, fhir_payment_notice, imis_payment):
        fhir_payment_notice['created'] = f'{imis_payment.date_created}'

    @classmethod
    def build_fhir_request(cls, fhir_payment_notice, imis_payment, reference_type):
        imis_invoice = cls._fetch_invoice_related_to_payment(imis_payment)
        fhir_payment_notice.request = cls.build_fhir_resource_reference(
            imis_invoice.subject,
            type="Invoice",
            reference_type=reference_type
        )

    @classmethod
    def build_fhir_payment(cls, fhir_payment_notice, imis_payment):
        json_ext = imis_payment.json_ext
        if json_ext:
            if 'reconciliation' in json_ext:
                reconciliation_json_ext_dict = json_ext['reconciliation']
                if 'id' in reconciliation_json_ext_dict:
                    reference = Reference.construct()
                    resource_type = "PaymentReconciliation"
                    resource_id = reconciliation_json_ext_dict['id']
                    reference.reference = f'{resource_type}/{resource_id}'
                    fhir_payment_notice["payment"] = reference

    @classmethod
    def build_fhir_payment_date(cls, fhir_payment_notice, imis_payment):
        fhir_payment_notice.paymentDate = f'{imis_payment.date_payment}'

    @classmethod
    def build_fhir_amount(cls, fhir_payment_notice, imis_payment):
        fhir_payment_notice["amount"] = cls.build_fhir_money(imis_payment.amount_received)

    @classmethod
    def build_fhir_payment_status(cls, fhir_payment_notice, imis_payment):
        paymentStatus = PaymentNoticePaymentStatusMapping.\
            to_fhir_status[imis_payment.reconciliation_status]
        fhir_payment_notice.paymentStatus = cls.build_codeable_concept(
            code=paymentStatus,
            display=paymentStatus,
            system="http://terminology.hl7.org/CodeSystem/paymentstatus"
        )

    @classmethod
    def build_fhir_recipient(cls, fhir_payment_notice):
        default_insurance_organisation = DEFAULT_CFG['R4_fhir_insurance_organisation_config']
        reference = Reference.construct()
        resource_type = "Organization"
        resource_id = default_insurance_organisation['id']
        reference.reference = f'{resource_type}/{resource_id}'
        fhir_payment_notice["recipient"] = reference

    @classmethod
    def get_reference_obj_uuid(cls, imis_payment):
        return imis_payment.id

    @classmethod
    def get_reference_obj_id(cls, imis_payment):
        return imis_payment.id

    @classmethod
    def get_fhir_resource_type(cls):
        return PaymentNotice

    @classmethod
    def _fetch_invoice_related_to_payment(cls, imis_payment):
        imis_invoices = imis_payment.invoice_payments.all()
        imis_invoice = None
        for invoice in imis_invoices:
            imis_invoice = invoice
        return imis_invoice
