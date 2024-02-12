from api_fhir_r4.configurations import BaseConfiguration
from api_fhir_r4.defaultConfig import DEFAULT_CFG
from django.conf import settings


class GeneralConfiguration(BaseConfiguration):

    @classmethod
    def build_configuration(cls, cfg):
        config = cls.get_config()
        config.default_audit_user_id = cfg['default_audit_user_id']
        config.gender_codes = cfg['gender_codes']
        config.base_url = cfg['base_url']
        config.default_value_of_patient_head_attribute = cfg['default_value_of_patient_head_attribute']
        config.default_value_of_patient_card_issued_attribute = cfg['default_value_of_patient_card_issued_attribute']
        config.default_value_of_location_offline_attribute = cfg['default_value_of_location_offline_attribute']
        config.default_value_of_location_care_type = cfg['default_value_of_location_care_type']
        config.default_response_page_size = cfg['default_response_page_size']
        config.claim_rule_engine_validation = cfg['claim_rule_engine_validation']
        config.subscribe_insuree_signal = cfg['subscribe_insuree_signal']

    @classmethod
    def get_default_audit_user_id(cls):
        return cls.get_config_attribute("default_audit_user_id")

    @classmethod
    def get_male_gender_code(cls):
        return cls.get_config_attribute("gender_codes").get('male', 'M')

    @classmethod
    def get_female_gender_code(cls):
        return cls.get_config_attribute("gender_codes").get('female', 'F')

    @classmethod
    def get_other_gender_code(cls):
        return cls.get_config_attribute("gender_codes").get('other', 'O')

    @classmethod
    def get_default_value_of_patient_head_attribute(cls):
        return cls.get_config_attribute("default_value_of_patient_head_attribute")

    @classmethod
    def get_default_value_of_patient_card_issued_attribute(cls):
        return cls.get_config_attribute("default_value_of_patient_card_issued_attribute")

    @classmethod
    def get_default_value_of_location_offline_attribute(cls):
        return cls.get_config_attribute("default_value_of_location_offline_attribute")

    @classmethod
    def get_default_value_of_location_care_type(cls):
        return cls.get_config_attribute("default_value_of_location_care_type")

    @classmethod
    def get_default_response_page_size(cls):
        return cls.get_config_attribute("default_response_page_size")

    @classmethod
    def get_claim_rule_engine_validation(cls):
        return cls.get_config_attribute("claim_rule_engine_validation")

    @classmethod
    def show_system(cls):
        return 1

    @classmethod
    def get_system_base_url(cls):
        return cls.get_config_attribute("base_url")

    @classmethod
    def get_host_domain(cls):
        url = cls.get_base_url()
        if url.startswith('/'):
            return f'http://{settings.SITE_URL()}'
        else:
            return ''

    @classmethod        
    def get_base_url(cls):
        MODULE_NAME = 'api_fhir_r4'
        site_root = settings.SITE_ROOT()
        if site_root is not None:
            base_url = '/' + site_root
        if base_url.endswith('/'):
            return base_url + MODULE_NAME + '/'
        else:
            return base_url + '/'+MODULE_NAME+'/'

    @classmethod
    def get_subscribe_insuree_signal(cls):
        return cls.get_config_attribute("subscribe_insuree_signal")
