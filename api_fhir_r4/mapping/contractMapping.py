from api_fhir_r4.configurations import GeneralConfiguration, R4CoverageConfig
from django.utils.translation import gettext as _
from policy.models import Policy


class ContractStatus(object):

    contract_status = {
        f"{Policy.STATUS_ACTIVE}": R4CoverageConfig.get_status_policy_code(),
        f"{Policy.STATUS_IDLE}": R4CoverageConfig.get_status_offered_code(),
        f"{Policy.STATUS_EXPIRED}": R4CoverageConfig.get_status_terminated_code(),
        f"{Policy.STATUS_SUSPENDED}": R4CoverageConfig.get_status_disputed_code(),
    }

    @classmethod
    def imis_map_status(cls, code, imis_policy):
        status = {
            R4CoverageConfig.get_status_idle_code(): imis_policy.STATUS_IDLE,
            R4CoverageConfig.get_status_active_code(): imis_policy.STATUS_ACTIVE,
            R4CoverageConfig.get_status_suspended_code(): imis_policy.STATUS_SUSPENDED,
            R4CoverageConfig.get_status_expired_code(): imis_policy.STATUS_EXPIRED,
        }
        return status[code]


class ContractState(object):

    contract_state = {
        f"{Policy.STAGE_NEW}": R4CoverageConfig.get_status_offered_code(),
        f"{Policy.STAGE_RENEWED}": R4CoverageConfig.get_status_renewed_code(),
    }

    @classmethod
    def imis_map_stage(cls, code, imis_policy):
        codes = {
            R4CoverageConfig.get_status_offered_code(): imis_policy.STAGE_NEW,
            R4CoverageConfig.get_status_active_code(): imis_policy.STAGE_RENEWED
        }
        return codes[code]


class PayTypeMapping(object):

    pay_type = {
        "B": _("Bank transfer"),
        "C": _("Cash"),
        "M": _("Mobile phone"),
        "F": _("Funding")
    }
