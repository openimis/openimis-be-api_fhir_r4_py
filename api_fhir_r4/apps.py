import logging
from collections import OrderedDict

import yaml
from django.apps import AppConfig

from api_fhir_r4.configurations import ModuleConfiguration
from api_fhir_r4.defaultConfig import DEFAULT_CFG
from core.rights_declaration import RightsDeclaration

logger = logging.getLogger(__name__)

MODULE_NAME = "api_fhir_r4"


# Rights, by entity then by action.
#
# This module has almost no rights of its own: its REST/FHIR layer *borrows* those of
# the business modules (claim, insuree, policy, location, medical, product, invoice,
# policyholder, core) - see `api_fhir_r4/rights.py`. Those rights are NOT redeclared
# here: their source of truth is the owning module's `DJANGO_PERMS`, and they are
# reached through `Model.get_rights(action)`. Redeclaring a borrowing would make it a
# second definition, free to diverge with nothing to report it.
#
# The FHIR subscription is the only entity this module owns: it is a purely FHIR
# concept (no GraphQL equivalent), its model lives here and its four rights
# (158001-158004) are in block 158 of permissions_map.json.
DJANGO_PERMS = {
    "subscription": {
        "query": ("api_fhir_r4.view_subscription", 158001),
        "create": ("api_fhir_r4.add_subscription", 158002),
        "update": ("api_fhir_r4.change_subscription", 158003),
        "delete": ("api_fhir_r4.delete_subscription", 158004),
    },
}

# The config keys keep their historical name (`fhir_sub_*_perms`): they are read by
# `R4SubscriptionConfig.get_fhir_sub_*_perms()` and named in permissions_map.json under
# "api_fhir_r4.fhir_sub_search/create/update/delete".
_PERM_CFG = {
    "fhir_sub_search_perms": ("subscription", "query"),
    "fhir_sub_create_perms": ("subscription", "create"),
    "fhir_sub_update_perms": ("subscription", "update"),
    "fhir_sub_delete_perms": ("subscription", "delete"),
}

RIGHTS = RightsDeclaration(MODULE_NAME, DJANGO_PERMS, _PERM_CFG)

perms = RIGHTS.perms
django_perms = RIGHTS.django_perm_names
configured_perms = RIGHTS.configured
require = RIGHTS.require


class ApiFhirConfig(AppConfig):
    # FHIR subscription rights: constants, as everywhere else. They used to live in
    # the nested "R4_fhir_subscription_config" block of defaultConfig and were read by
    # `R4SubscriptionConfig.get_fhir_sub_*_perms()`, so they were still overridable -
    # `get_or_default`'s filter only looks at the top level. That was also the last
    # place `collect_all_gql_permissions` had to read a config from.
    fhir_sub_search_perms = RIGHTS.perms("subscription", "query")
    fhir_sub_create_perms = RIGHTS.perms("subscription", "create")
    fhir_sub_update_perms = RIGHTS.perms("subscription", "update")
    fhir_sub_delete_perms = RIGHTS.perms("subscription", "delete")

    name = MODULE_NAME

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__configure_module(cfg)
        setup_yaml()

        from openIMIS.ExceptionHandlerRegistry import ExceptionHandlerRegistry
        from .exceptions.fhir_api_exception_handler import fhir_api_exception_handler

        ExceptionHandlerRegistry.register_exception_handler(
            MODULE_NAME, fhir_api_exception_handler
        )

    def __configure_module(self, cfg):
        ModuleConfiguration.build_configuration(cfg)
        logger.info(f"Module {MODULE_NAME} configured successfully")


def setup_yaml():
    def represent_ordered_dict(dumper, data):
        return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())

    yaml.SafeDumper.add_representer(OrderedDict, represent_ordered_dict)
