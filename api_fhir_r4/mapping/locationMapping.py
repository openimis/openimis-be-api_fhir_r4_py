from api_fhir_r4.configurations import GeneralConfiguration, R4LocationConfig
from api_fhir_r4.models.imisModelEnums import ImisLocationType


class LocationTypeMapping:
    SYSTEM = f'{GeneralConfiguration.get_system_base_url()}StructureDefinition/openimis-location'
    PHYSICAL_TYPE_SYSTEM = f'{GeneralConfiguration.get_system_base_url()}/CodeSystem/location-type'

    PHYSICAL_TYPES_DEFINITIONS = {
        ImisLocationType.REGION.value: {
            'code': R4LocationConfig.get_fhir_code_for_region(),
            'display': 'Region',
            'system': PHYSICAL_TYPE_SYSTEM
        },
        ImisLocationType.DISTRICT.value: {
            'code': R4LocationConfig.get_fhir_code_for_district(),
            'display': 'District',
            'system': PHYSICAL_TYPE_SYSTEM
        },
        ImisLocationType.WARD.value: {
            'code': R4LocationConfig.get_fhir_code_for_ward(),
            'display': 'Municipality/Ward',
            'system': PHYSICAL_TYPE_SYSTEM
        },
        ImisLocationType.VILLAGE.value: {
            'code': R4LocationConfig.get_fhir_code_for_village(),
            'display': 'Village',
            'system': PHYSICAL_TYPE_SYSTEM
        }
    }
