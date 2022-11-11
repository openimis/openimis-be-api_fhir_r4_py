from api_fhir_r4.configurations import PaymentNoticeConfiguration


class R4PaymentNoticeConfig(PaymentNoticeConfiguration):
    _config = 'R4_fhir_payment_notice_config'

    @classmethod
    def build_configuration(cls, cfg):
        cls.get_config().R4_fhir_payment_notice_config = cfg['R4_fhir_payment_notice_config']

    @classmethod
    def get_fhir_payment_notice_status_active(cls):
        return cls.get_config_attribute('R4_fhir_payment_notice_config')\
            .get('fhir_payment_notice_status_active', 'active')

    @classmethod
    def get_fhir_payment_notice_status_cancelled(cls):
        return cls.get_config_attribute('R4_fhir_payment_notice_config')\
            .get('fhir_payment_notice_status_cancelled', 'cancelled')

    @classmethod
    def get_fhir_payment_notice_status_draft(cls):
        return cls.get_config_attribute('R4_fhir_payment_notice_config')\
            .get('fhir_payment_notice_status_draft', 'draft')

    @classmethod
    def get_fhir_payment_notice_status_entered_in_error(cls):
        return cls.get_config_attribute('R4_fhir_payment_notice_config')\
            .get('fhir_payment_notice_status_entered_in_error', 'entered-in-error')

    @classmethod
    def get_fhir_payment_notice_payment_status_paid(cls):
        return cls.get_config_attribute('R4_fhir_payment_notice_config') \
            .get('fhir_payment_notice_payment_status_paid', 'paid')

    @classmethod
    def get_fhir_payment_notice_payment_status_cleared(cls):
        return cls.get_config_attribute('R4_fhir_payment_notice_config') \
            .get('fhir_payment_notice_payment_status_cleared', 'cleared')
