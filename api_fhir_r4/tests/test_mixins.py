from unittest.mock import patch, MagicMock

from django.test import TestCase

from fhir.resources.R4B import FHIRAbstractModel

from api_fhir_r4.serializers import PatientSerializer


class ContainedContentHelper(object):
    @staticmethod
    def build_test_converter(returned_obj=FHIRAbstractModel.construct()):
        converter = MagicMock()
        converter.convert_from_source = MagicMock(name='convert_from_source', return_value=[returned_obj])
        return converter


class ContainedContentSerializerMixinTestCase(TestCase):
    from api_fhir_r4.containedResources.serializerMixin import ContainedContentSerializerMixin

    class BaseTestSerializer:
        context = {'contained': True}

        def to_representation(self, obj):
            return FHIRAbstractModel.construct().dict()

    class TestSerializer(ContainedContentSerializerMixin, BaseTestSerializer):

        @property
        def contained_resources(self):
            from api_fhir_r4.containedResources.containedResources import AbstractContainedResourceCollection
            class TestContainedResource(AbstractContainedResourceCollection):
                @classmethod
                def _definitions_for_serializers(cls):
                    from api_fhir_r4.containedResources.containedResources import ContainedResourceDefinition
                    return {
                        PatientSerializer: ContainedResourceDefinition('insuree', 'Patient')
                    }

            return TestContainedResource

    def test_resource_transformation(self):
        test_serializer = self.TestSerializer()
        test_imis_obj = MagicMock()
        test_imis_obj.insuree = MagicMock()
        representation = test_serializer.to_representation(test_imis_obj)

        expected_outcome = {'contained': []}
        self.assertEqual(dict(representation), expected_outcome)
