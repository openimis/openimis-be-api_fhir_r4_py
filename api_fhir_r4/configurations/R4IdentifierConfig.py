from api_fhir_r4.configurations import IdentifierConfiguration


class R4IdentifierConfig(IdentifierConfiguration):

    @classmethod
    def build_configuration(cls, cfg):
        cls.get_config().R4_fhir_identifier_type_config = cfg['R4_fhir_identifier_type_config']

    @classmethod
    def get_fhir_identifier_type_system(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('system',
                                                                "https://hl7.org/fhir/valueset-identifier-type.html")

    @classmethod
    def get_fhir_acsn_type_code(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_db_id_type', "ACSN")

    @classmethod
    def get_fhir_id_type_code(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_db_id_type', "ACSN")

    @classmethod
    def get_fhir_chfid_type_code(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_chfid_type', "SB")

    @classmethod
    def get_fhir_passport_type_code(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_passport_type', "PPN")

    @classmethod
    def get_fhir_facility_id_type(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_facility_id_type', "FI")

    @classmethod
    def get_fhir_claim_admin_code_type(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_claim_admin_code_type', "FILL")

    @classmethod
    def get_fhir_claim_code_type(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_claim_code_type', "MR")

    @classmethod
    def get_fhir_uuid_type_code(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_db_uuid_type', "UUID")

    @classmethod
    def get_fhir_location_code_type(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_location_code_type', "LC")

    @classmethod
    def get_fhir_diagnosis_code_type(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_diagnosis_code_type', "DC")

    @classmethod
    def get_fhir_item_code_type(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_item_code_type', "IC")

    @classmethod
    def get_fhir_service_code_type(cls):
        return cls.get_config_attribute("R4_fhir_identifier_type_config").get('fhir_code_for_imis_service_code_type', "SC")
