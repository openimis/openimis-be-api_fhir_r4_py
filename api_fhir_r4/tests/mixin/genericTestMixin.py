from abc import ABC

from django.test import TestCase


class GenericTestMixin(TestCase, ABC):  # pragma: no cover
   
    def create_test_imis_instance(self):
        raise NotImplementedError('`test_imis_instance()` must be implemented.')

    def verify_imis_instance(self, imis_obj):
        raise NotImplementedError('`verify_imis_instance()` must be implemented.')

    def create_test_fhir_instance(self):
        raise NotImplementedError('`test_fhir_instance()` must be implemented.')

    def verify_fhir_instance(self, fhir_obj):
        raise NotImplementedError('`verify_fhir_instance()` must be implemented.')
