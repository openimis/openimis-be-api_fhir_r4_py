from api_fhir_r4.configurations import GeneralConfiguration


class ItemTypeMapping(object):
    item_type = {
        "D": "Drug",
        "M": "Medical_Consumable",
    }


class ItemContextlevel:
    SYSTEM = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/medication-level"

    item_context_level_coding = {
        "system": SYSTEM,
        "code": "M",
        "display": "Medication",
    }


class ItemVenueTypeMapping(object):
    item_venue_type = {
        "AMB": "ambulatory",
        "IMP": "IMP",
        "B": "both",
    }

    venue_fhir_imis = {
        "AMB": "O",
        "IMP": "I",
    }
