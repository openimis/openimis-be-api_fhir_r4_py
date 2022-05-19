import copy
from functools import lru_cache
from urllib.parse import urljoin

from api_fhir_r4.configurations import GeneralConfiguration, R4OrganisationConfig
from api_fhir_r4.models.imisModelEnums import ContactPointSystem
from policyholder.apps import PolicyholderConfig
from policyholder.services import PolicyHolderActivity, PolicyHolderLegalForm


class HealthFacilityOrganizationTypeMapping:
    LEGAL_FORM_CODE = 'D'
    LEGAL_FORM_DISPLAY = 'District organization'
    LEGAL_FORM_SYSTEM = 'CodeSystem/organization-legal-form'
    LEGAL_FORM_URL = f'{GeneralConfiguration.get_system_base_url()}StructureDefinition/organization-legal-form'

    LEGAL_FORM_MAPPING = {
        'C': 'Charity',
        'D': 'District Organization',
        'G': 'Government',
        'P': 'Private organization'
    }

    ORGANIZATION_TYPE = 'prov'

    EMAIL_CONTACT_POINT_SYSTEM = ContactPointSystem.EMAIL
    PHONE_CONTACT_POINT_SYSTEM = ContactPointSystem.PHONE
    FAX_CONTACT_POINT_SYSTEM = ContactPointSystem.FAX

    ADDRESS_LOCATION_REFERENCE_URL = \
        f'{GeneralConfiguration.get_system_base_url()}/StructureDefinition/address-location-reference'

    CONTRACT_PURPOSE = {
        'code': 'PAYOR',
        'system': 'http://terminology.hl7.org/CodeSystem/contactentity-type'
    }

    LEVEL_DISPLAY_MAPPING = {
        'D': 'Dispensary',
        'C': 'Health Centre',
        'H': 'Hospital'
    }

    LEVEL_SYSTEM = f'{GeneralConfiguration.get_system_base_url()}/CodeSystem/organization-hf-level'

    TYPE_SYSTEM = f'{GeneralConfiguration.get_system_base_url()}/CodeSystem/organization-hf-care-type'

    TYPE_DISPLAY_MAPPING = {
        'O': 'Out-patient',
        'I': 'In-patient',
        'B': 'Both'
    }


class PolicyHolderConfigMapping:
    @classmethod
    def _get_system(cls):
        raise NotImplementedError('_get_system() not implemented')

    @classmethod
    def _get_config_mapping(cls):
        raise NotImplementedError('_get_config_mapping() not implemented')

    @classmethod
    def fhir_ph_code_system(cls, code):
        @lru_cache(maxsize=None)
        def __code_system_dict():
            system = urljoin(
                GeneralConfiguration.get_system_base_url(),
                cls._get_system()
            )
            dict_ = {}
            for activity in copy.deepcopy(cls._get_config_mapping()):
                activity['system'] = system
                dict_[int(activity['code'])] = activity
            return dict_

        return __code_system_dict()[code]


class PolicyHolderOrganisationLegalFormMapping(PolicyHolderConfigMapping):
    @classmethod
    def _get_system(cls):
        return R4OrganisationConfig.get_fhir_ph_organisation_legal_form_code_system()

    @classmethod
    def _get_config_mapping(cls):
        return PolicyholderConfig.policyholder_legal_form


class PolicyHolderOrganisationActivityMapping(PolicyHolderConfigMapping):
    @classmethod
    def _get_system(cls):
        return R4OrganisationConfig.get_fhir_ph_organisation_activity_code_system()

    @classmethod
    def _get_config_mapping(cls):
        return PolicyholderConfig.policyholder_activity
