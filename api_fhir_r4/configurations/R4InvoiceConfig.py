from api_fhir_r4.configurations import InvoiceConfiguration


class R4InvoiceConfig(InvoiceConfiguration):
    @classmethod
    def build_configuration(cls, cfg):
        cls.get_config().R4_fhir_invoice_config = cfg['R4_fhir_invoice_config']

    @classmethod
    def get_fhir_invoice_type_system(cls):
        return cls.get_config_attribute("R4_fhir_invoice_config").get('fhir_invoice_type_system',
                                                                      "CodeSystem/invoice-type")

    @classmethod
    def get_fhir_invoice_charge_item_system(cls):
        return cls.get_config_attribute("R4_fhir_invoice_config").get('fhir_invoice_charge_item_system',
                                                                      "CodeSystem/invoice-charge-item")

    @classmethod
    def get_fhir_bill_type_system(cls):
        return cls.get_config_attribute("R4_fhir_invoice_config").get('fhir_bill_type_system',
                                                                      "CodeSystem/bill-type")

    @classmethod
    def get_fhir_bill_charge_item_system(cls):
        return cls.get_config_attribute("R4_fhir_invoice_config").get('fhir_bill_charge_item_system',
                                                                      "CodeSystem/bill-charge-item")

    @classmethod
    def get_subscribe_invoice_signal(cls):
        return cls.get_config_attribute("R4_fhir_invoice_config").get('subscribe_invoice_signal', False)
