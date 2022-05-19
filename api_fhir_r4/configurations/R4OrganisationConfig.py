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
    def get_fhir_ph_organisation_contactentity_type(cls):
        return cls.get_config_attribute('R4_fhir_organisation_config') \
            .get('fhir_ph_organisation_type_contactentity_type',
                 'http://terminology.hl7.org/CodeSystem/contactentity-type')

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

    @classmethod
    def get_fhir_insurer_organisation_id(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('id', 'openIMIS-Implementation')

    @classmethod
    def get_fhir_insurer_organisation_code(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('code', 'openIMIS')

    @classmethod
    def get_fhir_insurer_organisation_name(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('name', 'openIMIS Implementation')

    @classmethod
    def get_fhir_insurer_organisation_type(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('type', 'ins')

    @classmethod
    def get_fhir_insurer_organisation_email(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('email', 'implementation@openimis.org')

    @classmethod
    def get_fhir_insurer_organisation_phone(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('phone', '0908060703')

    @classmethod
    def get_fhir_insurer_organisation_fax(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('fax', '0908060730')

    @classmethod
    def get_fhir_insurer_organisation_contact_name(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('contact_name', 'Manuel D. Medina')

    @classmethod
    def get_fhir_insurer_organisation_municipality(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('municipality', 'Jamu')

    @classmethod
    def get_fhir_insurer_organisation_city(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('city', 'Jamula')

    @classmethod
    def get_fhir_insurer_organisation_district(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('district', 'Rapta')

    @classmethod
    def get_fhir_insurer_organisation_state(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('state', 'Ultha')

    @classmethod
    def get_fhir_insurer_organisation_line(cls):
        return cls.get_config_attribute('R4_fhir_insurance_organisation_config') \
            .get('line', '1 Pasay')
