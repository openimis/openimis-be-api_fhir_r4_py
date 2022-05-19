from api_fhir_r4.configurations import CoverageConfiguration


class R4CoverageConfig(CoverageConfiguration):

    @classmethod
    def build_configuration(cls, cfg):
        cls.get_config().R4_fhir_identifier_type_config = cfg['R4_fhir_coverage_config']
        cls.get_config().R4_fhir_contract_config = cfg['R4_fhir_contract_config']

    @classmethod
    def get_status_policy_code(cls):
        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_contract_policy_status', "Policy")

    @classmethod
    def get_status_executable_code(cls):
        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_contract_executable_status', "Executable")

    @classmethod
    def get_status_terminated_code(cls):

        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_contract_terminated_status', "Terminated")

    @classmethod
    def get_status_disputed_code(cls):
        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_contract_disputed_status', "Disputed")

    @classmethod
    def get_status_offered_code(cls):
        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_contract_offered_status', "Offered")

    @classmethod
    def get_status_renewed_code(cls):
        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_contract_renewed_status', "Renewed")

    @classmethod
    def get_signer_eo_type_code(cls):
        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_contract_eo_signer_type', "EnrolmentOfficer")

    @classmethod
    def get_signer_head_type_code(cls):
        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_contract_head_signer_type', "HeadOfFamily")

    @classmethod
    def get_offer_insuree_role_code(cls):
        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_contract_insuree_role', "Insuree")

    @classmethod
    def get_offer_dependant_role_code(cls):
        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_contract_dependant_role', "Dependant")

    @classmethod
    def get_organization_code(cls):
        return cls.get_config_attribute("R4_fhir_contract_config").get('fhir_organization_code', "openIMIS")

    @classmethod
    def get_family_reference_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_family_refereence_code', "FamilyReference")

    @classmethod
    def get_status_idle_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_status_idle_code', "Idle")

    @classmethod
    def get_status_cancelled_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_status_cancelled_code', "cancelled")

    @classmethod
    def get_status_draft_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_status_draft_code', "draft")

    @classmethod
    def get_status_active_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_status_active_code', "active")

    @classmethod
    def get_status_suspended_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_status_suspended_code', "suspended")

    @classmethod
    def get_status_expired_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_status_expired_code', "Expired")

    @classmethod
    def get_item_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_item_code', "item")

    @classmethod
    def get_service_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_service_code', "service")

    @classmethod
    def get_practitioner_role_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_practitioner_role_code', "Practitioner")

    @classmethod
    def get_product_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_product_code', "Product")

    @classmethod
    def get_enroll_date_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_enroll_date_code', "EnrollDate")

    @classmethod
    def get_effective_date_code(cls):
        return cls.get_config_attribute("R4_fhir_claim_config").get('fhir_effective_date_code', "EffectiveDate")

