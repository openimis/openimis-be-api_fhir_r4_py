from api_fhir_r4.configurations import LocationConfiguration


class R4LocationConfig(LocationConfiguration):

    @classmethod
    def build_configuration(cls, cfg):
        cls.get_config().R4_fhir_location_type = cfg['R4_fhir_location_site_type']
        cls.get_config().R4_fhir_location_physical_type = cfg['R4_fhir_location_physical_type']
        cls.get_config().R4_fhir_hf_service_type = cfg['R4_fhir_hf_service_type']
        cls.get_config().R4_fhir_location_status_codes = cfg['R4_fhir_location_status_codes']
        cls.get_config().R4_fhir_location_subscribe_signal = cfg['R4_fhir_location_subscribe_signal']

    @classmethod
    def get_fhir_location_site_type_system(cls):
        return cls.get_config_attribute("R4_fhir_location_type")\
            .get('system', "http://hl7.org/fhir/v3/ServiceDeliveryLocationRoleType/vs.html")

    @classmethod
    def get_fhir_code_for_hospital(cls):
        return cls.get_config_attribute("R4_fhir_location_type").get('fhir_code_for_hospital', "HOSP")

    @classmethod
    def get_fhir_code_for_dispensary(cls):
        return cls.get_config_attribute("R4_fhir_location_type").get('fhir_code_for_dispensary', "COMM")

    @classmethod
    def get_fhir_code_for_health_center(cls):
        return cls.get_config_attribute("R4_fhir_location_type").get('fhir_code_for_health_center', "OF")

    @classmethod
    def get_fhir_location_area_type_system(cls):
        return cls.get_config_attribute("R4_fhir_location_type")\
            .get('system', "https://openimis.atlassian.net/wiki/spaces/OP/pages/1389297887/FHIR+r4+-+Location")

    @classmethod
    def get_fhir_code_for_region(cls):
        return cls.get_config_attribute("R4_fhir_location_type").get('fhir_code_for_region', "R")

    @classmethod
    def get_fhir_code_for_district(cls):
        return cls.get_config_attribute("R4_fhir_location_type").get('fhir_code_for_district', "D")

    @classmethod
    def get_fhir_code_for_ward(cls):
        return cls.get_config_attribute("R4_fhir_location_type").get('fhir_code_for_ward', "W")

    @classmethod
    def get_fhir_code_for_village(cls):
        return cls.get_config_attribute("R4_fhir_location_type").get('fhir_code_for_village', "V")

    @classmethod
    def get_fhir_location_physical_type_system(cls):
        return cls.get_config_attribute("R4_fhir_location_physical_type")\
            .get('system', "https://openimis.github.io/openimis_fhir_r4_ig/CodeSystem/location-type")

    @classmethod
    def get_fhir_code_for_site(cls):
        return cls.get_config_attribute("R4_fhir_location_type").get('fhir_code_for_site', "si")
    
    @classmethod
    def get_fhir_code_for_area(cls):
        return cls.get_config_attribute("R4_fhir_location_type").get('fhir_code_for_area', "area")

# This should be part organisation because this is not related to the buiilding

    @classmethod
    def get_fhir_hf_service_type_system(cls):
        return cls.get_config_attribute("R4_fhir_hf_service_type")\
            .get('system', "http://hl7.org/fhir/valueset-service-type.html")

    @classmethod
    def get_fhir_code_for_in_patient(cls):
        return cls.get_config_attribute("R4_fhir_hf_service_type").get('fhir_code_for_in_patient', "I")

    @classmethod
    def get_fhir_code_for_out_patient(cls):
        return cls.get_config_attribute("R4_fhir_hf_service_type").get('fhir_code_for_out_patient', "O")

    @classmethod
    def get_fhir_code_for_both(cls):
        return cls.get_config_attribute("R4_fhir_hf_service_type").get('fhir_code_for_both', "B")

    @classmethod
    def get_fhir_code_for_active(cls):
        return cls.get_config_attribute("R4_fhir_location_status_codes").get('fhir_code_for_active', 'active')

    @classmethod
    def get_fhir_code_for_inactive(cls):
        return cls.get_config_attribute("R4_fhir_location_status_codes").get('fhir_code_for_inactive', 'inactive')

    @classmethod
    def get_subscribe_location_signal(cls):
        return cls.get_config_attribute("R4_fhir_location_subscribe_signal")
