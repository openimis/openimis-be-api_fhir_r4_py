from abc import ABC
from insuree.test_helpers import (
    create_test_gender,
    create_test_profession,
    create_test_education,
    create_test_relation,
    create_test_confirmation_type
)
from location.test_helpers import (
    create_basic_test_locations,
    create_test_basic_health_facility_legal_form,
    create_test_basic_health_facility_sub_level
)

from django.test import TestCase


class GenericTestMixin(TestCase, ABC):  # pragma: no cover

    @classmethod
    def setUpTestData(cls):
        super(GenericTestMixin, cls).setUpTestData()
        create_basic_test_locations()
        create_test_basic_health_facility_legal_form()
        create_test_basic_health_facility_sub_level()
        create_test_gender()
        create_test_profession()
        create_test_education()
        create_test_relation()
        create_test_confirmation_type()

    def create_test_imis_instance(self):
        raise NotImplementedError("`test_imis_instance()` must be implemented.")

    def verify_imis_instance(self, imis_obj):
        raise NotImplementedError("`verify_imis_instance()` must be implemented.")

    def create_test_fhir_instance(self):
        raise NotImplementedError("`test_fhir_instance()` must be implemented.")

    def verify_fhir_instance(self, fhir_obj):
        raise NotImplementedError("`verify_fhir_instance()` must be implemented.")
