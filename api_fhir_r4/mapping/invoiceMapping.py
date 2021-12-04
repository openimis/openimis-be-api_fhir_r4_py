from urllib.parse import urljoin

from django.utils.translation import gettext as _

from api_fhir_r4.configurations import GeneralConfiguration, R4InvoiceConfig


class ChargeItemMapping(object):
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
