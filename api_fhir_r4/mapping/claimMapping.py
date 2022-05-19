from api_fhir_r4.configurations import R4ClaimConfig, GeneralConfiguration
from claim.models import Claim
from django.utils.translation import gettext as _
from urllib.parse import urljoin


class ClaimPriorityMapping:
    SYSTEM = 'http://terminology.hl7.org/CodeSystem/processpriority'

    fhir_priority_coding = {
        'normal': {
            'system': SYSTEM,
            'code': 'normal',
            'display': 'Normal',
        }
    }


class ClaimVisitTypeMapping:
    SYSTEM = urljoin(GeneralConfiguration.get_system_base_url(), R4ClaimConfig.get_fhir_claim_visit_type_system())

    fhir_claim_visit_type_coding = {
        'E': {
            'system': SYSTEM,
            'code': 'E',
            'display': 'Emergency',
        },
        'R': {
            'system': SYSTEM,
            'code': 'R',
            'display': 'Referrals',
        },
        'O': {
            'system': SYSTEM,
            'code': 'O',
            'display': 'Other',
        }
    }


class ClaimItemCategoryMapping:
    SYSTEM = urljoin(GeneralConfiguration.get_system_base_url(), R4ClaimConfig.get_fhir_claim_item_category_system())

    fhir_claim_item_type_coding = {
        R4ClaimConfig.get_fhir_claim_item_code(): {
            'system': SYSTEM,
            'code': R4ClaimConfig.get_fhir_claim_item_code(),
            'display': 'Item',
        },
        R4ClaimConfig.get_fhir_claim_service_code(): {
            'system': SYSTEM,
            'code': R4ClaimConfig.get_fhir_claim_service_code(),
            'display': 'Service',
        }
    }


class ClaimResponseMapping(object):

    claim_status_system = f'{GeneralConfiguration.get_system_base_url()}CodeSystem/claim-status'
    claim_status = {
        f"{Claim.STATUS_REJECTED}": R4ClaimConfig.get_fhir_claim_status_rejected_code(),
        f"{Claim.STATUS_ENTERED}": R4ClaimConfig.get_fhir_claim_status_entered_code(),
        f"{Claim.STATUS_CHECKED}": R4ClaimConfig.get_fhir_claim_status_checked_code(),
        f"{Claim.STATUS_PROCESSED}": R4ClaimConfig.get_fhir_claim_status_processed_code(),
        f"{Claim.STATUS_VALUATED}": R4ClaimConfig.get_fhir_claim_status_valuated_code()
    }

    claim_outcome = {
        f"{Claim.STATUS_REJECTED}": _("complete"),
        f"{Claim.STATUS_ENTERED}": _("queued"),
        f"{Claim.STATUS_CHECKED}": _("partial"),
        f"{Claim.STATUS_PROCESSED}": _("partial"),
        f"{Claim.STATUS_VALUATED}": _("complete")
    }

    visit_type_system = f'{GeneralConfiguration.get_system_base_url()}CodeSystem/claim-visit-type'
    visit_type = {
        "E": _("Emergency"),
        "R": _("Referrals"),
        "O": _("Other"),
    }

    rejection_reason_system = f'{GeneralConfiguration.get_system_base_url()}CodeSystem/claim-rejection-reasons'
    rejection_reason = {
        -2: _("REJECTED BY AI EVALUATION"),
        -1: _("REJECTED BY MEDICAL OFFICER"),
        0: _("ACCEPTED"),
        1: _("INVALID ITEM OR SERVICE"),
        2: _("NOT IN PRICE LIST"),
        3: _("NO PRODUCT FOUND"),
        4: _("CATEGORY LIMITATION"),
        5: _("FREQUENCY FAILURE"),
        6: _("DUPLICATED"),
        7: _("FAMILY"),
        8: _("DIAGNOSIS NOT IN LIST"),
        9: _("TARGET DATE"),
        10: _("CARE TYPE"),
        11: _("MAX HOSPITAL ADMISSIONS"),
        12: _("MAX VISITS"),
        13: _("MAX CONSULTATIONS"),
        14: _("MAX SURGERIES"),
        15: _("MAX DELIVERIES"),
        16: _("QTY OVER LIMIT"),
        17: _("WAITING PERIOD FAIL"),
        19: _("MAX ANTENATAL"),
    }

