import logging
from collections import OrderedDict

import yaml
from django.apps import AppConfig

from api_fhir_r4.configurations import ModuleConfiguration
from api_fhir_r4.defaultConfig import DEFAULT_CFG
from core.rights_declaration import RightsDeclaration

logger = logging.getLogger(__name__)

MODULE_NAME = "api_fhir_r4"


# Droits, par entite puis par action.
#
# Ce module n'a presque pas de droits a lui : sa couche REST/FHIR *emprunte* ceux des
# modules metier (claim, insuree, policy, location, medical, product, invoice,
# policyholder, core) - voir `api_fhir_r4/rights.py`. Ces droits-la ne sont PAS
# redeclares ici : leur source de verite est le `DJANGO_PERMS` du module proprietaire,
# et on y accede par `Model.get_rights(action)`. Redeclarer un emprunt en ferait une
# seconde definition qui pourrait diverger sans que rien ne le signale.
#
# La souscription FHIR est la seule entite qui appartienne a ce module : c'est un
# concept purement FHIR (pas d'equivalent GraphQL), son modele vit ici et ses quatre
# droits (158001-158004) sont dans le bloc 158 de permissions_map.json.
DJANGO_PERMS = {
    "subscription": {
        "query": ("api_fhir_r4.view_subscription", 158001),
        "create": ("api_fhir_r4.add_subscription", 158002),
        "update": ("api_fhir_r4.change_subscription", 158003),
        "delete": ("api_fhir_r4.delete_subscription", 158004),
    },
}

# Les cles de config gardent leur nom historique (`fhir_sub_*_perms`) : elles sont lues
# par `R4SubscriptionConfig.get_fhir_sub_*_perms()` et nommees dans permissions_map.json
# sous "api_fhir_r4.fhir_sub_search/create/update/delete".
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
    # Droits des souscriptions FHIR : constantes, comme partout ailleurs. Ils vivaient
    # dans le bloc imbriqué "R4_fhir_subscription_config" du defaultConfig et étaient
    # lus par `R4SubscriptionConfig.get_fhir_sub_*_perms()`, donc encore surchargeables
    # - le filtre de `get_or_default` ne regarde que le premier niveau. C'était aussi
    # le dernier endroit d'où `collect_all_gql_permissions` devait lire une config.
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
