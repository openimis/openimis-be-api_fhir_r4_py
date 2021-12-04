from api_fhir_r4.configurations import OrganisationConfiguration


class R4OrganisationConfig(OrganisationConfiguration):

    @classmethod
    def build_configuration(cls, cfg):
        cls.get_config().R4_fhir_organisation_config = cfg['R4_fhir_organisation_config']

    @classmethod
    def get_fhir_ph_organisation_type(cls):
        return cls.get_config_attribute('R4_fhir_organisation_config').get('fhir_ph_organisation_type', 'bus')

    @classmethod
    def get_fhir_ph_organisation_type_system(cls):
        return cls.get_config_attribute('R4_fhir_organisation_config') \
            .get('fhir_ph_organisation_type_system',
                 'http://terminology.hl7.org/CodeSystem/organization-type')

    @classmethod
    def get_fhir_address_municipality_extension_system(cls):
        return cls.get_config_attribute('R4_fhir_organisation_config').get('fhir_address_municipality_extension_system',
                                                                           'StructureDefinition/address-municipality')

    @classmethod
    def get_fhir_location_reference_extension_system(cls):
        return cls.get_config_attribute('R4_fhir_organisation_config') \
            .get('fhir_location_reference_extension_system',
                 'StructureDefinition/address-location-reference')

    @classmethod
    def get_fhir_ph_organisation_legal_form_extension_system(cls):
        return cls.get_config_attribute('R4_fhir_organisation_config') \
            .get('fhir_ph_organisation_legal_form_extension_system',
                 'StructureDefinition/organization-ph-legal-form')

    @classmethod
    def get_fhir_ph_organisation_activity_extension_system(cls):
        return cls.get_config_attribute('R4_fhir_organisation_config') \
            .get('fhir_ph_organisation_activity_extension_system',
                 'StructureDefinition/organization-ph-activity')

    @classmethod
    def get_fhir_ph_organisation_legal_form_code_system(cls):
        return cls.get_config_attribute('R4_fhir_organisation_config') \
            .get('fhir_ph_organisation_legal_form_code_system',
                 'CodeSystem/organization-ph-legal-form')

    @classmethod
    def get_fhir_ph_organisation_activity_code_system(cls):
        return cls.get_config_attribute('R4_fhir_organisation_config') \
            .get('fhir_ph_organisation_activity_code_system',
                 'CodeSystem/organization-ph-activity')
