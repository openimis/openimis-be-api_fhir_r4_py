import json
from api_fhir_r4.configurations import CoverageEligibilityConfiguration


class R4CoverageEligibilityConfiguration(CoverageEligibilityConfiguration):

    @classmethod
    def build_configuration(cls, cfg):
        cls.get_config().R4_fhir_coverage_eligibility_config = cfg['R4_fhir_coverage_eligibility_config']

    @classmethod
    def get_serializer(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_serializer')

    @classmethod
    def get_fhir_financial_code(cls):
        pass

    @classmethod
    def get_fhir_item_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_item_code', 'item')

    @classmethod
    def get_fhir_service_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_service_code', 'service')

    @classmethod
    def get_fhir_total_admissions_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_total_admissions_code', 'total_admissions')

    @classmethod
    def get_fhir_total_visits_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_total_visits_code', 'total_visits')

    @classmethod
    def get_fhir_total_consultations_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_total_consultations_code', 'total_consultations')

    @classmethod
    def get_fhir_total_surgeries_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_total_surgeries_code', 'total_surgeries')

    @classmethod
    def get_fhir_total_deliveries_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_total_deliveries_code', 'total_deliveries')

    @classmethod
    def get_fhir_total_antenatal_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_total_antenatal_code', 'total_antenatal')

    @classmethod
    def get_fhir_consultation_amount_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_consultation_amount_code',
                                                                 'consultation_amount')

    @classmethod
    def get_fhir_surgery_amount_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_surgery_amount_code', 'surgery_amount')

    @classmethod
    def get_fhir_delivery_amount_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_delivery_amount_code', 'delivery_amount')

    @classmethod
    def get_fhir_hospitalization_amount_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_hospitalization_amount_code',
                                                                 'hospitalization_amount')

    @classmethod
    def get_fhir_antenatal_amount_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_antenatal_amount_code', 'antenatal_amount')

    @classmethod
    def get_fhir_service_left_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_service_left_code', 'service_left')

    @classmethod
    def get_fhir_item_left_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_item_left_code', 'item_left')

    @classmethod
    def get_fhir_is_item_ok_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_is_item_ok_code', 'is_item_ok')

    @classmethod
    def get_fhir_is_service_ok_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_is_service_ok_code', 'is_service_ok')

    @classmethod
    def get_fhir_balance_code(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_balance_code', 'balance')

    @classmethod
    def get_fhir_balance_default_category(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_balance_default_category', 'medical')

    @classmethod
    def get_fhir_active_policy_status(cls):
        return cls.get_config_attribute("R4_fhir_coverage_eligibility_config").get('fhir_active_policy_status', ('A', 2))
