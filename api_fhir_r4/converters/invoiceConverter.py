from fhir.resources.annotation import Annotation
from fhir.resources.extension import Extension
from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from fhir.resources.invoice import Invoice as FHIRInvoice, \
    InvoiceLineItem as FHIRInvoiceLineItem, InvoiceLineItemPriceComponent
from fhir.resources.money import Money
from api_fhir_r4.mapping.invoiceMapping import InvoiceChargeItemMapping, InvoiceTypeMapping, BillTypeMapping, \
    BillChargeItemMapping
from api_fhir_r4.utils import DbManagerUtils
from insuree.models import Insuree
from invoice.models import Invoice


class GenericInvoiceConverter(BaseFHIRConverter, ReferenceConverterMixin):
    @classmethod
    def to_imis_obj(cls, data, audit_user_id):
        raise NotImplementedError('to_imis_obj() not implemented.')

    @classmethod
    def to_fhir_obj(cls, imis_invoice, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_invoice = {"status": "active"}
        fhir_invoice = FHIRInvoice(**fhir_invoice)
        cls.build_fhir_identifiers(fhir_invoice, imis_invoice)
        cls.build_fhir_pk(fhir_invoice, imis_invoice, reference_type)
        cls.build_fhir_type(fhir_invoice, imis_invoice)
        cls.build_fhir_recipient(fhir_invoice, imis_invoice, reference_type)
        cls.build_fhir_date(fhir_invoice, imis_invoice)
        cls.build_fhir_totals(fhir_invoice, imis_invoice)
        cls.build_fhir_line_items(fhir_invoice, imis_invoice, imis_invoice.currency_code)
        cls.build_fhir_note(fhir_invoice, imis_invoice)
        return fhir_invoice

    @classmethod
    def get_reference_obj_uuid(cls, imis_invoice):
        return imis_invoice.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_invoice):
        return imis_invoice.uuid

    @classmethod
    def get_reference_obj_code(cls, imis_invoice):
        return imis_invoice.code

    @classmethod
    def get_fhir_resource_type(cls):
        return FHIRInvoice

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        invoice_uuid = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Invoice, uuid=invoice_uuid)

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

    @classmethod
    def build_fhir_identifiers(cls, fhir_invoice, imis_invoice):
        identifiers = []
        cls.build_fhir_uuid_identifier(identifiers, imis_invoice)
        cls.build_fhir_code_identifier(identifiers, imis_invoice)
        fhir_invoice.identifier = identifiers

    @classmethod
    def build_fhir_type(cls, fhir_invoice, imis_invoice):
        invoice_type = cls.get_type_mapping()[imis_invoice.subject_type.model]
        fhir_invoice.type = cls.build_codeable_concept_from_coding(cls.build_fhir_mapped_coding(invoice_type))

    @classmethod
    def build_fhir_recipient(cls, fhir_invoice, imis_invoice, reference_type):
        if isinstance(imis_invoice.thirdparty, Insuree):
            reference_resource = 'Patient'
        else:
            reference_resource = 'Organization'

        fhir_invoice.recipient = cls.build_fhir_resource_reference(
            imis_invoice.thirdparty,
            type=reference_resource,
            reference_type=reference_type)

    @classmethod
    def build_fhir_date(cls, fhir_invoice, imis_invoice):
        fhir_invoice.date = cls.get_invoice_date(imis_invoice)

    @classmethod
    def build_fhir_totals(cls, fhir_invoice, imis_invoice):
        fhir_invoice.totalNet = cls.build_fhir_money(imis_invoice.amount_net, imis_invoice.currency_code)
        fhir_invoice.totalGross = cls.build_fhir_money(imis_invoice.amount_total, imis_invoice.currency_code)

    @classmethod
    def build_fhir_line_items(cls, fhir_invoice, imis_invoice, currency):
        fhir_invoice.lineItem = []
        for line in cls.get_invoice_line_items(imis_invoice):
            fhir_line_item = FHIRInvoiceLineItem.construct()
            cls.build_line_item_charge_item_codeable_concept(fhir_line_item, line)
            fhir_line_item.priceComponent = []
            cls.build_line_item_price_component_base(fhir_line_item, line, currency)
            if line.tax_rate:
                cls.build_line_item_price_component_tax(fhir_line_item, line, currency)
            if line.discount:
                cls.build_line_item_price_component_discount(fhir_line_item, line, currency)
            if line.deduction:
                cls.build_line_item_price_component_deduction(fhir_line_item, line, currency)
            fhir_invoice.lineItem.append(fhir_line_item)

    @classmethod
    def build_line_item_charge_item_codeable_concept(cls, fhir_line_item, line_item):
        charge_item = cls.get_charge_item_mapping()[line_item.line_type.model]
        codeable_concept = cls.build_codeable_concept_from_coding(cls.build_fhir_mapped_coding(charge_item))
        fhir_line_item.chargeItemCodeableConcept = codeable_concept

    @classmethod
    def build_line_item_price_component_base(cls, fhir_line_item, line_item, currency):
        price_component = cls.build_line_item_price_component(
            "base",
            line_item.quantity,
            line_item.unit_price * line_item.quantity,
            currency
        )
        price_component.code = cls.build_codeable_concept(
            code="Code",
            display=line_item.code,
            system="Code"
        )
        price_component.extension = [cls.build_line_item_unit_price_extension(line_item, currency)]
        fhir_line_item.priceComponent.append(price_component)

    @classmethod
    def build_line_item_price_component_discount(cls, fhir_line_item, line_item, currency):
        price_component = cls.build_line_item_price_component(
            "discount",
            line_item.discount,
            -line_item.unit_price * line_item.quantity * line_item.discount,
            currency
        )
        price_component.extension = [cls.build_line_item_unit_price_extension(line_item, currency)]
        fhir_line_item.priceComponent.append(price_component)

    @classmethod
    def build_line_item_price_component_deduction(cls, fhir_line_item, line_item, currency):
        price_component = cls.build_line_item_price_component(
            "deduction",
            1,
            -line_item.deduction,
            currency
        )
        price_component.extension = [cls.build_line_item_unit_price_extension(line_item, currency)]
        fhir_line_item.priceComponent.append(price_component)

    @classmethod
    def build_line_item_price_component_tax(cls, fhir_line_item, line_item, currency):
        price_component = cls.build_line_item_price_component(
            "tax",
            line_item.tax_rate,
            ((line_item.quantity * line_item.unit_price * (1 - (line_item.discount or 0))) - (
                    line_item.deduction or 0)) * line_item.tax_rate,
            currency
        )
        price_component.extension = [cls.build_line_item_unit_price_extension(line_item, currency)]
        fhir_line_item.priceComponent.append(price_component)

    @classmethod
    def build_line_item_price_component(cls, component_type, factor, amount, currency):
        price_component = {"type": component_type}
        price_component = InvoiceLineItemPriceComponent(**price_component)
        price_component.factor = factor
        price_component.amount = cls.build_fhir_money(amount, currency)
        return price_component

    @classmethod
    def build_line_item_unit_price_extension(cls, line_item, currency):
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}/StructureDefinition/unit-price"
        unit_price = Money.construct()
        unit_price.value = line_item.unit_price
        unit_price.currency = currency
        extension.valueMoney = unit_price
        return extension

    @classmethod
    def build_fhir_note(cls, fhir_invoice, imis_invoice):
        if imis_invoice.note:
            annotation = Annotation.construct()
            annotation.text = imis_invoice.note
            fhir_invoice.note = [annotation]

    @classmethod
    def get_type_mapping(cls):
        raise NotImplementedError('get_type_mapping() not implemented')

    @classmethod
    def get_charge_item_mapping(cls):
        raise NotImplementedError('get_charge_item_mapping() not implemented')

    @classmethod
    def get_invoice_date(cls, invoice):
        raise NotImplementedError('get_invoice_date() not implemented')

    @classmethod
    def get_invoice_line_items(cls, invoice):
        raise NotImplementedError('get_invoice_date() not implemented')


class InvoiceConverter(GenericInvoiceConverter):
    @classmethod
    def get_type_mapping(cls):
        return InvoiceTypeMapping.invoice_type

    @classmethod
    def get_charge_item_mapping(cls):
        return InvoiceChargeItemMapping.charge_item

    @classmethod
    def get_invoice_date(cls, invoice):
        return invoice.date_invoice

    @classmethod
    def get_invoice_line_items(cls, invoice):
        return invoice.line_items.all()


class BillInvoiceConverter(GenericInvoiceConverter):
    @classmethod
    def get_type_mapping(cls):
        return BillTypeMapping.invoice_type

    @classmethod
    def get_charge_item_mapping(cls):
        return BillChargeItemMapping.charge_item

    @classmethod
    def get_invoice_date(cls, invoice):
        return invoice.date_bill

    @classmethod
    def get_invoice_line_items(cls, invoice):
        return invoice.line_items_bill.all()
