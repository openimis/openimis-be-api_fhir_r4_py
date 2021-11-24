DEFAULT_CFG = {
    "default_audit_user_id": 1,
    "gender_codes": {
        "male": "M",
        "female": "F",
        "other": "O"
    },
    "default_value_of_patient_head_attribute": False,
    "default_value_of_patient_card_issued_attribute": False,
    "default_value_of_location_offline_attribute": False,
    "default_value_of_location_care_type": "B",
    "default_response_page_size": 10,
    "R4_fhir_identifier_type_config": {
        "system": "https://hl7.org/fhir/valueset-identifier-type.html",
        "fhir_code_for_imis_db_uuid_type": "UUID",
        "fhir_code_for_imis_db_id_type": "ACSN",
        "fhir_code_for_imis_chfid_type": "SB",
        "fhir_code_for_imis_passport_type": "PPN",
        "fhir_code_for_imis_facility_id_type": "FI",
        "fhir_code_for_imis_claim_admin_code_type": "FILL",
        "fhir_code_for_imis_claim_code_type": "MR",
        "fhir_code_for_imis_location_code_type": "LC",
        "fhir_code_for_imis_diagnosis_code_type": "DC",
        "fhir_code_for_imis_item_code_type": "IC",
        "fhir_code_for_imis_service_code_type": "SC"
    },
    "R4_fhir_marital_status_config": {
        "system": "http://hl7.org/fhir/valueset-marital-status.html",
        "fhir_code_for_married": "M",
        "fhir_code_for_never_married": "S",
        "fhir_code_for_divorced": "D",
        "fhir_code_for_widowed": "W",
        "fhir_code_for_unknown": "U"
    },
    "R4_fhir_location_site_type": {
        "system": "http://hl7.org/fhir/v3/ServiceDeliveryLocationRoleType/vs.html",
        "fhir_code_for_hospital": "HOSP",
        "fhir_code_for_dispensary": "COMM",
        "fhir_code_for_health_center": "OF",
    },
    "R4_fhir_location_physical_type": {
        "system": "http://terminology.hl7.org/CodeSystem/location-physical-type.html",
        "fhir_code_for_region": "R",
        "fhir_code_for_district": "D",
        "fhir_code_for_ward": "W",
        "fhir_code_for_village": "V"
    },
    "R4_fhir_hf_service_type": {
        "system": "http://hl7.org/fhir/valueset-service-type.html",
        "fhir_code_for_in_patient": "I",
        "fhir_code_for_out_patient": "O",
        "fhir_code_for_both": "B"
    },
    "R4_fhir_issue_type_config": {
        "fhir_code_for_exception": "exception",
        "fhir_code_for_not_found": "not-found",
        "fhir_code_for_informational": "informational"
    },
    "R4_fhir_claim_config": {
        "fhir_claim_information_guarantee_id_code": "guarantee_id",
        "fhir_claim_information_explanation_code": "explanation",
        "fhir_claim_item_explanation_code": "item_explanation",
        "fhir_claim_item_code": "item",
        "fhir_claim_service_code": "service",
        "fhir_claim_status_rejected_code": "rejected",
        "fhir_claim_status_entered_code": "entered",
        "fhir_claim_status_checked_code": "checked",
        "fhir_claim_status_processed_code": "processed",
        "fhir_claim_status_valuated_code": "valuated",
        "fhir_claim_item_status_code": "claim_item_status",
        "fhir_claim_item_status_passed_code": "passed",
        "fhir_claim_item_status_rejected_code": "rejected",
        "fhir_claim_item_general_adjudication_code": "general",
        "fhir_claim_item_rejected_reason_adjudication_code": "rejected_reason",
        "fhir_claim_organization_code": "openIMIS",
        "fhir_claim_attachment_code": "attachment",
        "fhir_claim_information_category_system": "http://terminology.hl7.org/CodeSystem/claiminformationcategory",
        "fhir_claim_allowed_mime_types_regex":
            '|'.join(['text\/.*', 'image\/png', 'image\/jpe?g', 'application\/msword', '.*doc.*'])
    },
    "R4_fhir_coverage_eligibility_config": {
        "fhir_serializer": "PolicyCoverageEligibilityRequestSerializer",
        "fhir_item_code": "item",
        "fhir_service_code": "service",
        "fhir_total_admissions_code": "total_admissions",
        "fhir_total_visits_code": "total_visits",
        "fhir_total_consultations_code": "total_consultations",
        "fhir_total_surgeries_code": "total_surgeries",
        "fhir_total_deliveries_code": "total_deliveries",
        "fhir_total_antenatal_code": "total_antenatal",
        "fhir_consultation_amount_code": "consultation_amount",
        "fhir_surgery_amount_code": "surgery_amount",
        "fhir_delivery_amount_code": "delivery_amount",
        "fhir_hospitalization_amount_code": "hospitalization_amount",
        "fhir_antenatal_amount_code": "antenatal_amount",
        "fhir_service_left_code": "service_left",
        "fhir_item_left_code": "item_left",
        "fhir_is_item_ok_code": "is_item_ok",
        "fhir_is_service_ok_code": "is_service_ok",
        "fhir_balance_code": "balance",
        "fhir_balance_default_category": "medical",
        "fhir_active_policy_status": ("A", 2)
    },
    "R4_fhir_communication_request_config": {
        "fhir_care_rendered_code": "care_rendered",
        "fhir_payment_asked_code": "payment_asked",
        "fhir_drug_prescribed_code": "drug_prescribed",
        "fhir_drug_received_code": "drug_received",
        "fhir_asessment_code": "asessment"
    },
    "R4_fhir_contract_config": {
        "fhir_contract_eo_signer_type":"EnrolmentOfficer",
        "fhir_contract_head_signer_type":"HeadOfFamily",
        "fhir_contract_insuree_role":"Insuree",
        "fhir_contract_dependant_role":"Dependant",
        "fhir_contract_executable_status":"Executable",
        "fhir_contract_renewed_status":"Renewed",
        "fhir_contract_policy_status":"Policy",
        "fhir_contract_Terminated_status":"Terminated"
    },
    "R4_fhir_coverage_config": {
        "fhir_family_refereence_code": "FamilyReference",
        "fhir_status_idle_code": "Idle",
        "fhir_status_active_code": "Active",
        "fhir_status_suspended_code": "Suspended",
        "fhir_status_expired_code": "Expired",
        "fhir_status_disputed_code": "Disputed",
        "fhir_item_code": "item",
        "fhir_service_code": "service",
        "fhir_practitioner_role_code": "Practitioner",
        "fhir_product_code": "Product",
        "fhir_effective_date_code": "EffectiveDate",
        "fhir_enroll_date_code": "EnrollDate"
    }
}