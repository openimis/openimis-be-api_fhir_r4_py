import logging

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

    def __configure_module(self, cfg):
        ModuleConfiguration.build_configuration(cfg)
        logger.info('Module $s configured successfully', MODULE_NAME)
