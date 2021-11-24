"""
from django.utils.translation import gettext
from api_fhir_r4.converters import BaseFHIRConverter
from api_fhir_r4.exceptions import FHIRRequestProcessException
from api_fhir_r4.models import BankAccount


class OrganisationConverterMixin(object):
    @classmethod
    def build_bank(cls,data):
        account={}
        account['bank'] = data.bank
        account['no']  = data.no
        return account
"""