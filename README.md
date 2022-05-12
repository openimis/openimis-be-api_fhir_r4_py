# openIMIS Backend FHIR R4 API reference module

| Note |
| --- |
|This repository currently supports basic functionality of FHIR R4 API and might miss some openIMIS specific validations. Please use it with caution if you want to connect it to a production database.|

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

[![Maintainability](https://img.shields.io/codeclimate/maintainability/openimis/openimis-be-api_fhir_py.svg)](https://codeclimate.com/github/openimis/openimis-be-api_fhir_py/maintainability)
[![Test Coverage](https://img.shields.io/codeclimate/coverage/openimis/openimis-be-api_fhir_py.svg)](https://codeclimate.com/github/openimis/openimis-be-api_fhir_py)

## Description
This repository holds the files of the openIMIS Backend FHIR R4 API reference module. 
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

The module is mapping objects between openIMIS and FHIR R4 representation, 
and allows external applications to use HL7 FHIR R4 standardised communication protocol 
when interacting with openIMIS.

## Documentation
The documentation for this module can be found at [openIMIS Wiki page](https://openimis.atlassian.net/wiki/spaces/OP/pages/1233649676/openIMIS+FHIR+R4+Overview+Page).

## Resource Available

Location

Coverage
Contract
Patient
Practitioner
PractitionerRole

Claim
ClaimResponse
Medication
HealthcareService
Condition
ActivityDefinition

CommunicationRequest
CoverageEligibilityRequest


## Implementation setup
This module is published on Python Package Index as [openimis-be-api-fhir_r4](https://pypi.org/project/openimis-be-api-fhir_r4).

The FHIR R4 API will be available after the module is deployed on [openimis-be_py](https://github.com/openimis/openimis-be_py). 
Check the [openimis-be_py](https://github.com/openimis/openimis-be_py) 's readme file on how to activate the module 
(add the 'api_fhir_r4' module to [openimis.json](https://github.com/openimis/openimis-be_py/blob/master/openimis.json)) 
and start the openIMIS backend. 

## Configurations Options
| Configuration key                              | Description                                                                              | Default value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|------------------------------------------------|------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| default_audit_user_id                          | default value which will be used for 'audit_user_id' field                               | "default_audit_user_id": 1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| gender_codes                                   | configuration of codes used by the openIMIS to represent gender (male, female, other)    | "gender_codes": {     "male": "M",     "female": "F",     "other": "O" }                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| R4_fhir_identifier_type_config                 | configuration of system and codes used to represent the specific types of identifiers    | "R4_fhir_identifier_type_config":{    "system":"https://hl7.org/fhir/valueset-identifier-type.html",    "fhir_code_for_imis_db_uuid_type": "UUID",    "fhir_code_for_imis_db_id_type":"ACSN",    "fhir_code_for_imis_chfid_type":"SB",    "fhir_code_for_imis_passport_type":"PPN",    "fhir_code_for_imis_facility_id_type":"FI",    "fhir_code_for_imis_claim_admin_code_type":"FILL",    "fhir_code_for_imis_claim_code_type":"MR"    "fhir_code_for_imis_location_code_type": "LC",    "fhir_code_for_imis_diagnosis_code_type": "DC",    "fhir_code_for_imis_item_code_type": "IC",    "fhir_code_for_imis_service_code_type": "SC"}                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| R4_fhir_marital_status_config                  | configuration of system and codes used to represent the specific types of marital status | "R4_fhir_marital_status_config":{    "system":"http://hl7.org/fhir/valueset-marital-status.html",    "fhir_code_for_married":"M",    "fhir_code_for_never_married":"S",    "fhir_code_for_divorced":"D",    "fhir_code_for_widowed":"W",    "fhir_code_for_unknown":"U"}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| R4_fhir_location_site_type                     | configuration of system and codes used to represent the specific types of location role  | "R4_fhir_location_role_type": {    "system": "http://hl7.org/fhir/v3/ServiceDeliveryLocationRoleType/vs.html",    "fhir_code_for_hospital": "HOSP",    "fhir_code_for_dispensary": "COMM",    "fhir_code_for_health_center": "OP"}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| R4_fhir_location_physical_type                 | configurations of system and codes used to represent the specific types of location physical types  | "R4_fhir_location_physical_type": {    "system": "http://terminology.hl7.org/CodeSystem/location-physical-type.html",    "fhir_code_for_region": "R",    "fhir_code_for_district": "D",    "fhir_code_for_ward": "W",    "fhir_code_for_village": "V"}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| R4_fhir_contract_config						 | configuration of system and codes used to represent the specific contract role, state and status |         "fhir_contract_eo_signer_type":"EnrolmentOfficer",        "fhir_contract_head_signer_type":"HeadOfFamily",        "fhir_contract_insuree_role":"Insuree",        "fhir_contract_executable_status":"Executable",        "fhir_contract_renewed_status":"Renewed",        "fhir_contract_policy_status":"Policy",        "fhir_contract_Terminated_status":"Terminated" |
| R4_fhir_hf_service_type                        | configuration of system and codes used to represent the specific types of services       | "R4_fhir_hf_service_type": {    "system": "http://hl7.org/fhir/valueset-service-type.html",    "fhir_code_for_in_patient": "I",    "fhir_code_for_out_patient": "O",    "fhir_code_for_both": "B"}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| R4_fhir_issue_type_config                      | configuration of system and codes used to represent the specific types of operation outcome  | "R4_fhir_issue_type_config": {    "fhir_code_for_exception": "exception",    "fhir_code_for_not_found": "not-found",    "fhir_code_for_informational": "informational"}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| R4_fhir_claim_config                           | configuration of system and codes used to represent the specific types of claim codes    | "R4_fhir_claim_config": {    "fhir_claim_information_guarantee_id_code": "guarantee_id",    "fhir_claim_information_explanation_code": "explanation",    "fhir_claim_item_explanation_code": "item_explanation",    "fhir_claim_item_code": "item",    "fhir_claim_service_code": "service",    "fhir_claim_status_rejected_code": "rejected",    "fhir_claim_status_entered_code": "entered",    "fhir_claim_status_checked_code": "checked",    "fhir_claim_status_processed_code": "processed",    "fhir_claim_status_valuated_code": "valuated",    "fhir_claim_item_status_code": "claim_item_status",    "fhir_claim_item_status_passed_code": "passed",    "fhir_claim_item_status_rejected_code": "rejected",    "fhir_claim_item_general_adjudication_code": "general",    "fhir_claim_item_rejected_reason_adjudication_code": "rejected_reason"}                                                                                                                                                                                                                                                     |
| R4_fhir_coverage_eligibility_config            | configuration of system and codes used to represent the specific codes used by eligibility endpoint  | "R4_fhir_coverage_eligibility_config": {    "fhir_serializer": "PolicyCoverageEligibilityRequestSerializer",    "fhir_item_code": "item",    "fhir_service_code": "service",    "fhir_total_admissions_code": "total_admissions",    "fhir_total_visits_code": "total_visits",    "fhir_total_consultations_code": "total_consultations",    "fhir_total_surgeries_code": "total_surgeries",    "fhir_total_deliveries_code": "total_deliveries",    "fhir_total_antenatal_code": "total_antenatal",    "fhir_consultation_amount_code": "consultation_amount",    "fhir_surgery_amount_code": "surgery_amount",    "fhir_delivery_amount_code": "delivery_amount",    "fhir_hospitalization_amount_code": "hospitalization_amount",    "fhir_antenatal_amount_code": "antenatal_amount",    "fhir_service_left_code": "service_left",    "fhir_item_left_code": "item_left",    "fhir_is_item_ok_code": "is_item_ok",    "fhir_is_service_ok_code": "is_service_ok",    "fhir_balance_code": "balance",    "fhir_balance_default_category": "medical",    "fhir_active_policy_status": ("A", 2)}   |
| R4_fhir_communication_request_config           | configuration of system and codes used to represent the specific codes for IMIS feedback attributes  | "R4_fhir_communication_request_config": {    "fhir_care_rendered_code": "care_rendered",    "fhir_payment_asked_code": "payment_asked",    "fhir_drug_prescribed_code": "drug_prescribed",    "fhir_drug_received_code": "drug_received",    "fhir_asessment_code": "asessment"}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| default_value_of_patient_head_attribute        | default value for 'head' attribute used for creating new Insuree object                  | "default_value_of_patient_head_attribute": False,                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| default_value_of_patient_card_issued_attribute | default value for 'card_issued' attribute used for creating new Insuree object           | "default_value_of_patient_card_issued_attribute": False,                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| default_value_of_location_care_type            | default value for 'location_care_type' attribute used for creating new Location object   | "default_value_of_location_care_type": "B"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| default_response_page_size                     | default value for a response page size                                                   | "default_response_page_size": 10                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |

## Example of usage
To fetch information about all openIMIS Insurees (as FHIR R4 Patients), send a  **GET** request on:
```bash
http://127.0.0.1:8000/api_fhir_r4/Patient/
```
`127.0.0.1:8000` is the server address (if run on your local host).

Example of response ([mapping description](https://openimis.atlassian.net/wiki/spaces/OP/pages/1389133931/FHIR+R4+-+Patient)):
```json
{
    "resourceType": "Patient",
    "address": [
        {
            "text": "",
            "type": "physical",
            "use": "home"
        },
        {
            "text": "0.0 0.0",
            "type": "both",
            "use": "home"
        }
    ],
    "birthDate": "1952-05-07",
    "extension": [
        {
            "url": "https://openimis.atlassian.net/wiki/spaces/OP/pages/960069653/FHIR+extension+isHead",
            "valueBoolean": false
        },
        {
            "url": "https://openimis.atlassian.net/wiki/spaces/OP/pages/960331779/FHIR+extension+registrationDate",
            "valueString": "2018-03-27T06:44:02.833000"
        },
        {
            "url": "https://openimis.atlassian.net/wiki/spaces/OP/pages/960495619/FHIR+extension+Location",
            "valueString": "R1D1M1V1"
        },
        {
            "url": "https://openimis.atlassian.net/wiki/spaces/OP/pages/960331788/FHIR+extension+Education",
            "valueString": ""
        },
        {
            "url": "https://openimis.atlassian.net/wiki/spaces/OP/pages/960135203/FHIE+extension+Profession",
            "valueString": ""
        }
    ],
    "gender": "female",
    "id": "3A16BEDC-3E51-459F-B89C-889EB2FE8E6F",
    "identifier": [
        {
            "type": {
                "coding": [
                    {
                        "code": "UUID",
                        "system": "https://hl7.org/fhir/valueset-identifier-type.html"
                    }
                ]
            },
            "use": "usual",
            "value": "3A16BEDC-3E51-459F-B89C-889EB2FE8E6F"
        },
        {
            "type": {
                "coding": [
                    {
                        "code": "SB",
                        "system": "https://hl7.org/fhir/valueset-identifier-type.html"
                    }
                ]
            },
            "use": "usual",
            "value": "070707081"
        },
        {
            "type": {
                "coding": [
                    {
                        "code": "PPN",
                        "system": "https://hl7.org/fhir/valueset-identifier-type.html"
                    }
                ]
            },
            "use": "usual",
            "value": ""
        }
    ],
    "link": [
        {
            "other": {
                "reference": "Patient/18BC40A1-A1AB-47AB-9BC0-9F3C0A7B1BDF"
            },
            "type": "Spouse"
        }
    ],
    "maritalStatus": {
        "coding": [
            {
                "code": "M",
                "system": "http://hl7.org/fhir/valueset-marital-status.html"
            }
        ]
    },
    "name": [
        {
            "family": "Macintyre",
            "given": [
                "Jane"
            ],
            "use": "usual"
        }
    ],
    "photo": [
        {
            "creation": "2018-03-27",
            "url": "Images\\Updated\\070707081_E00001_20180327_0.0_0.0.jpg"
        }
    ],
    "telecom": [
        {
            "system": "phone",
            "use": "home",
            "value": ""
        },
        {
            "system": "email",
            "use": "home",
            "value": ""
        }
    ]
}
```

## Subscriptions

FHIR API R4 module allows users to define subscriptions and receive notifications when new resources are created or 
updated. Currently, supported resources are:
- Patient
- Organisation (only of `bus` or HealthFacility type)
- Invoice (All Bill and Invoice types defined in `invoiceMapping.py`)

To use the subscription feature a user is required to have related subscription permissions and read permission for subscribed 
resource. To create a subscription the following payload should be sent to `/Subscription/` endpoint:
```JSON
{
    "status": "active",
    "end": "2030-01-01T00:00:00Z",
    "reason": "Invoice",
    "criteria": "Invoice?resourceType=policy",
    "channel": {
        "type": "rest-hook",
        "endpoint": "http://example.com/path",
        "header": [
            "{\"example\": \"1234\"}"
        ]
    }
}
```

Explanation of the payload:
- `status` - required to be `"active"`
- `end` - subscription expiration time (required to have datetime information, `Z` for UTC)
- `reason` - required to match subscribed resource name
- `criteria` - allows to filter resources that should be included in a notification (should match GET arguments format). 
  - To subscribe all resources of a given name, leave the same as `reason`
  - To subscribe all resources of a given type, include `resourceType` argument and specify a type. To subscribe multiple types of a given resource (but not all), create multiple subscriptions
  - You can specify additional filtering arguments after that. Currently, the format should match queryset filter keyword arguments of the underlying IMIS model
- `channel` - specify the target for notifications
  - `type` - currently the only supported type is `rest-hook`
  - `endpoint` - url to send notifications to (should allow POST method)
  - `header` - serialized json string specifying additional headers to be included in POST request, beside the standard HTTP headers (i.e. `Authentication` header with bearer token should be `"{\"Authentication\": \"bearer abcdef0123456789\"}"`). To not include any headers leave as `"{}"`.

# Dependencies
All required dependencies can be found in the [setup.py](https://github.com/openimis/openimis-be-api_fhir_r4_py/blob/master/setup.py) file.
