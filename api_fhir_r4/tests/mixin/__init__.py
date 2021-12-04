from unittest import TestCase


class FhirConverterTestMixin(TestCase):
    def verify_fhir_identifier(self, fhir_obj, identifier_type, expected_identifier_value):
        identifiers = [identifier for identifier in fhir_obj.identifier
                       if identifier.type.coding[0].code == identifier_type]
        self.assertEqual(len(identifiers), 1)
        self.assertEqual(identifiers[0].value, expected_identifier_value)

    def verify_fhir_coding_exists(self, fhir_coding, expected_code):
        self.assertIsNotNone(next(iter([coding for coding in fhir_coding if coding.code == expected_code]), None))
