from medical.models import Service

from api_fhir_r4.configurations import GeneralConfiguration


class ServiceTypeMapping(object):
    SYSTEM = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/activity-definition-service-type.html"

    fhir_service_type_coding = {
        Service.TYPE_PREVENTATIVE: {
            "system": SYSTEM,
            "code": "P",
            "display": "Preventive",
        },
        Service.TYPE_CURATIVE: {
            "system": SYSTEM,
            "code": "C",
            "display": "Curative",
        },
    }


class ServiceLevelMapping(object):
    SYSTEM = f"{GeneralConfiguration.get_system_base_url()}ValueSet/activity-definition-level"

    fhir_service_level_coding = {
        Service.LEVEL_SIMPLE_SERVICE: {
            "system": SYSTEM,
            "code": "S",
            "display": "Simple Service",
        },
        Service.LEVEL_VISIT: {
            "system": SYSTEM,
            "code": "V",
            "display": "Visit",
        },
        Service.LEVEL_DAY_HOSPITAL: {
            "system": SYSTEM,
            "code": "D",
            "display": "Day of stay",
        },
        Service.LEVEL_HOSPITAL_CARE: {
            "system": SYSTEM,
            "code": "H",
            "display": "Hospital case",
        },
    }


class UseContextMapping(object):
    SYSTEM = "http://terminology.hl7.org/CodeSystem/usage-context-type"

    fhir_use_context_coding = {
        "gender": {
            "system": SYSTEM,
            "code": "gender",
            "display": "Gender",
        },
        "age": {
            "system": SYSTEM,
            "code": "age",
            "display": "Age Range",
        },
        "venue": {
            "system": SYSTEM,
            "code": "venue",
            "display": "Clinical Venue",
        },
        "workflow": {
            "system": SYSTEM,
            "code": "workflow",
            "display": "Workflow Setting",
        },
    }


class VenueMapping(object):
    SYSTEM = "http://terminology.hl7.org/2.1.0/CodeSystem-v3-ActCode.html"

    fhir_venue_coding = {
        Service.CARE_TYPE_OUT_PATIENT: {
            "system": SYSTEM,
            "code": "AMB",
            "display": "ambulatory",
        },
        Service.CARE_TYPE_IN_PATIENT: {
            "system": SYSTEM,
            "code": "IMP",
            "display": "IMP",
        }
    }

    imis_venue_coding = {
        "AMB": Service.CARE_TYPE_OUT_PATIENT,
        "IMP": Service.CARE_TYPE_IN_PATIENT
    }


class WorkflowMapping(object):
    SYSTEM = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/activity-definition-usage-context-workflow-type"

    fhir_workflow_coding = {
        Service.CATEGORY_SURGERY: {
            "system": SYSTEM,
            "code": "S",
            "display": "Surgery",
        },
        Service.CATEGORY_CONSULTATION: {
            "system": SYSTEM,
            "code": "C",
            "display": "Consultations",
        },
        Service.CATEGORY_DELIVERY: {
            "system": SYSTEM,
            "code": "D",
            "display": "Delivery",
        },
        Service.CATEGORY_ANTENATAL: {
            "system": SYSTEM,
            "code": "A",
            "display": "Antenatal",
        },
        Service.CATEGORY_OTHER: {
            "system": SYSTEM,
            "code": "O",
            "display": "Other",
        },
    }
