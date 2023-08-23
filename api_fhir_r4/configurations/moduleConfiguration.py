from api_fhir_r4.configurations import BaseConfiguration, GeneralConfiguration, R4ApiFhirConfig


class ModuleConfiguration(BaseConfiguration):
    @classmethod
    def build_configuration(cls, cfg):
        GeneralConfiguration.build_configuration(cfg)
        cls.get_r4().build_configuration(cfg)

    @classmethod
    def get_r4(cls):
        return R4ApiFhirConfig
