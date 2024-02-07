import json
from pathlib import Path

from django.test import TestCase
from api_fhir_r4.tests.utils import load_and_replace_json


class FhirConverterTestMixin(TestCase):
    def verify_fhir_identifier(self, fhir_obj, identifier_type, expected_identifier_value):
        identifiers = [identifier for identifier in fhir_obj.identifier
                       if identifier.type.coding[0].code == identifier_type]
        self.assertEqual(len(identifiers), 1)
        self.assertEqual(str(identifiers[0].value), str(expected_identifier_value))

    def verify_fhir_coding_exists(self, fhir_coding, expected_code):
        self.assertIsNotNone(next(iter([coding for coding in fhir_coding if coding.code == expected_code]), None))


class ConvertToImisTestMixin:
    @property
    def converter(self):
        raise NotImplementedError()

    def create_test_fhir_instance(self):
        raise NotImplementedError()

    def verify_imis_instance(self, imis_instance):
        raise NotImplementedError()

    def test_to_imis_obj(self):
        fhir_instance = self.create_test_fhir_instance()
        imis_instance = self.converter.to_imis_obj(fhir_instance.dict(), None)
        self.verify_imis_instance(imis_instance)


class ConvertToFhirTestMixin:
    @property
    def converter(self):
        raise NotImplementedError()

    def create_test_imis_instance(self):
        raise NotImplementedError()

    def verify_fhir_instance(self, fhir_instance):
        raise NotImplementedError()

    def test_to_fhir_obj(self):
        imis_instance = self.create_test_imis_instance()
        fhir_instance = self.converter.to_fhir_obj(imis_instance)
        self.verify_fhir_instance(fhir_instance)


class ConvertJsonToFhirTestMixin:
    sub_str = {}
    @property
    def fhir_resource(self):
        raise NotImplementedError()

    @property
    def json_repr(self):
        raise NotImplementedError()

    def verify_fhir_instance(self, fhir_instance):
        raise NotImplementedError()

    def test_fhir_object_from_json(self):
        fhir_instance = self.fhir_resource.parse_obj(load_and_replace_json(self.json_repr, self.sub_str))
        self.verify_fhir_instance(fhir_instance)


