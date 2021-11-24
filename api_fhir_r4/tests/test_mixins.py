from unittest.mock import patch, MagicMock

from django.test import TestCase

from api_fhir_r4.mixins import ContainedContentSerializerMixin
from api_fhir_r4.models import FHIRBaseObject


class ContainedContentHelper(object):
    @staticmethod
    def build_test_converter(returned_obj=FHIRBaseObject()):
        converter = MagicMock()
        converter.convert_from_source = MagicMock(name='convert_from_source', return_value=[returned_obj])
        return converter


class ContainedContentSerializerMixinTestCase(TestCase):

    class BaseTestSerializer:
        context = {'contained': True}

        def to_representation(self, obj):
            return FHIRBaseObject().toDict()

    class TestSerializer(ContainedContentSerializerMixin, BaseTestSerializer):

        @property
        def contained_resources(self):
            return [
                ContainedContentHelper.build_test_converter()
            ]

    def test_resource_transformation(self):
        test_serializer = self.TestSerializer()
        test_imis_obj = MagicMock()
        representation = test_serializer.to_representation(test_imis_obj)

        expected_outcome = {'contained': [{}]}
        self.assertEqual(representation, expected_outcome)
