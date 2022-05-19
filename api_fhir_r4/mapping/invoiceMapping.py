from urllib.parse import urljoin

from django.utils.translation import gettext as _

from api_fhir_r4.configurations import GeneralConfiguration, R4InvoiceConfig


class InvoiceChargeItemMapping(object):
    SYSTEM = urljoin(GeneralConfiguration.get_system_base_url(), R4InvoiceConfig.get_fhir_invoice_charge_item_system())
    charge_item = {
        "policy": {
            "code": "policy",
            "display": _("Policy"),
            "system": SYSTEM
        },
        "contractcontributionplandetails": {
            "code": "contribution",
            "display": _("Contribution"),
            "system": SYSTEM
        },
    }


class InvoiceTypeMapping(object):
    SYSTEM = urljoin(GeneralConfiguration.get_system_base_url(), R4InvoiceConfig.get_fhir_invoice_type_system())

    invoice_type = {
        "family": {
            "code": "contribution",
            "display": _("Contribution"),
            "system": SYSTEM
        },
        "contract": {
            "code": "contract",
            "display": _("Contract"),
            "system": SYSTEM
        },
    }


class BillChargeItemMapping(object):
    SYSTEM = urljoin(GeneralConfiguration.get_system_base_url(), R4InvoiceConfig.get_fhir_bill_charge_item_system())
    charge_item = {
        "claim": {
            "code": "claim",
            "display": _("Claim"),
            "system": SYSTEM
        },
        "commission": {
            "code": "commission",
            "display": _("Commission"),
            "system": SYSTEM
        },
        "capitationpayment": {
            "code": "claim",
            "display": _("Claim"),
            "system": SYSTEM
        },
        "policy": {
            "code": "policy",
            "display": _("Policy"),
            "system": SYSTEM
        }
    }


class BillTypeMapping(object):
    SYSTEM = urljoin(GeneralConfiguration.get_system_base_url(), R4InvoiceConfig.get_fhir_bill_type_system())

    invoice_type = {
        "batchrun": {
            "code": "claim-batch",
            "display": _("Claim batch payment"),
            "system": SYSTEM
        },
        "commission": {
            "code": "commission",
            "display": _("Commission"),
            "system": SYSTEM
        },
        "fees": {
            "code": "fees",
            "display": _("Fees"),
            "system": SYSTEM
        },
        "policy": {
            "code": "policy",
            "display": _("Policy"),
            "system": SYSTEM
        }
    }
