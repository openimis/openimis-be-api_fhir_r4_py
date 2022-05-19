from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.models.imisModelEnums import ContactPointSystem


class HealthFacilityOrganizationTypeMapping:
    LEGAL_FORM_CODE = 'D'
    LEGAL_FORM_DISPLAY = 'District organization'
    LEGAL_FORM_SYSTEM = 'CodeSystem/organization-legal-form'
    LEGAL_FORM_URL = f'{GeneralConfiguration.get_system_base_url()}StructureDefinition/organization-legal-form'

    ORGANIZATION_TYPE = 'prov'

    EMAIL_CONTACT_POINT_SYSTEM = ContactPointSystem.EMAIL
    PHONE_CONTACT_POINT_SYSTEM = ContactPointSystem.PHONE
    FAX_CONTACT_POINT_SYSTEM = ContactPointSystem.FAX

    ADDRESS_LOCATION_REFERENCE_URL = \
        f'{GeneralConfiguration.get_system_base_url()}/StructureDefinition/address-location-reference'

    CONTRACT_PURPOSE = {
        'code': 'PAYOR',
        'system': 'http://terminology.hl7.org/CodeSystem/contactentity-type'
    }

    LEVEL_DISPLAY_MAPPING = {
        'D': 'Dispensary',
        'C': 'Health Centre',
        'H': 'Hospital'
    }

    TYPE_DISPLAY_MAPPING = {
        'O': 'Out-patient',
        'I': 'In-patient',
        'B': 'Both'
    }

    LEVEL_SYSTEM = f'{GeneralConfiguration.get_system_base_url()}/CodeSystem/organization-hf-level'

    TYPE_SYSTEM = f'{GeneralConfiguration.get_system_base_url()}/CodeSystem/organization-hf-care-type'
