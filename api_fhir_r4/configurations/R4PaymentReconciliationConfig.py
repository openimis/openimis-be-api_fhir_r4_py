from api_fhir_r4.configurations import PaymentReconciliationConfiguration


class R4PaymentReconciliationConfig(PaymentReconciliationConfiguration):
    _config = 'R4_fhir_payment_reconciliation_config'

    @classmethod
    def build_configuration(cls, cfg):
        cls.get_config().R4_fhir_payment_reconciliation_config = cfg['R4_fhir_payment_reconciliation_config']

    @classmethod
    def get_fhir_payment_reconciliation_url(cls):
        return cls.get_config_attribute('R4_fhir_payment_notice_config')\
            .get('get_fhir_payment_reconciliation_url', 'localhost/api/api_fhir_r4/')

    @classmethod
    def get_fhir_payment_reconciliation_token(cls):
        return cls.get_config_attribute('R4_fhir_payment_notice_config')\
            .get('get_fhir_payment_reconciliation_token', 'bearer token')
