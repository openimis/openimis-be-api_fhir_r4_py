from unittest.mock import MagicMock

from django.test import TestCase

from unittest import mock

from api_fhir_r4.converters import ContainedResourceConverter
from fhir.resources.fhirabstractmodel import FHIRAbstractModel


class ContainedResourceConverterTestCase(TestCase):

    @mock.patch('claim.models.Claim')
    @mock.patch('insuree.models.Insuree', spec=['Insuree'])
    @mock.patch('api_fhir_r4.converters.PatientConverter')
    def test_convert_from_source_single_component(self, claim_mock, insuree_mock, insuree_converter_mock):
        # Arrange
        test_attribute = 'insuree'
        test_fhir_object = FHIRAbstractModel.construct()

        #Act
        convert_result = self.__base_extract_conversion(claim_mock, insuree_mock, insuree_converter_mock,
                                                        test_attribute, test_fhir_object)

        # Assert
        claim_mock.__getattribute__.assert_called_once_with(test_attribute)
        insuree_converter_mock.to_fhir_obj.assert_called_once_with(insuree_mock, 'uuid_reference')

        self.assertEqual(len(convert_result), 1)
        self.assertEqual(convert_result[0], test_fhir_object)

    @mock.patch('claim.models.Claim')
    @mock.patch('insuree.models.Insuree', spec=['Insuree'])
    @mock.patch('api_fhir_r4.converters.PatientConverter')
    def test_convert_from_source_many_components(self, claim_mock, insuree_mock, insuree_converter_mock):
        # Arrange
        test_attribute = 'insuree'
        test_fhir_object = FHIRAbstractModel.construct()

        # Act
        convert_result = self.__base_extract_conversion(claim_mock, [insuree_mock]*3, insuree_converter_mock,
                                                        test_attribute, test_fhir_object)
        # fhir abstract model is unhashable
        unique_results = set()
        for result in convert_result:
            key = repr(result)
            if key not in unique_results:
                unique_results.add(key)
        unique_results = list(unique_results)

        # Assert
        claim_mock.__getattribute__.assert_called_once_with(test_attribute)
        calls = [mock.call(insuree_mock, 'uuid_reference')]*3
        insuree_converter_mock.to_fhir_obj.assert_has_calls(calls)

        self.assertEqual(len(convert_result), 3)
        self.assertEqual(len(unique_results), 1)
        self.assertEqual(unique_results[0], repr(test_fhir_object))

    def __base_extract_conversion(self, main_model, extracted_value, converter,
                                  test_attribute_name='insuree', test_fhir_conversion_result=FHIRAbstractModel.construct()):
        # Arrange
        test_attribute = test_attribute_name
        test_fhir_object = test_fhir_conversion_result
        insuree_converter_type = MagicMock('__init__', return_value=converter)
        main_model.__getattribute__ = MagicMock(name='__getattribute__', return_value=extracted_value)
        converter.to_fhir_obj = MagicMock(name='to_fhir_obj', return_value=test_fhir_object)
        converter.return_value = converter

        # Act
        resource_converter = ContainedResourceConverter(test_attribute, insuree_converter_type)
        convert_result = resource_converter.convert_from_source(main_model)
        return convert_result