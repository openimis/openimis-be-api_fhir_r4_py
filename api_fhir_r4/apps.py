import logging
from collections import OrderedDict

import yaml
from django.apps import AppConfig

from api_fhir_r4.configurations import ModuleConfiguration
from api_fhir_r4.defaultConfig import DEFAULT_CFG

logger = logging.getLogger(__name__)

MODULE_NAME = "api_fhir_r4"


class ApiFhirConfig(AppConfig):
    name = MODULE_NAME

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__configure_module(cfg)
        setup_yaml()

        from openIMIS.ExceptionHandlerRegistry import ExceptionHandlerRegistry
        from .exceptions.fhir_api_exception_handler import fhir_api_exception_handler
        ExceptionHandlerRegistry.register_exception_handler(MODULE_NAME, fhir_api_exception_handler)

    def __configure_module(self, cfg):
        ModuleConfiguration.build_configuration(cfg)
        logger.info(F'Module {MODULE_NAME} configured successfully')


def setup_yaml():
    def represent_ordered_dict(dumper, data):
        return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

    yaml.SafeDumper.add_representer(OrderedDict, represent_ordered_dict)
