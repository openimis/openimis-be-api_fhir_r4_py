import json
import os

from fhir.resources.activitydefinition import ActivityDefinition

from api_fhir_r4.converters import ActivityDefinitionConverter
from api_fhir_r4.tests.mixin.activityDefinitionTestMixin import ActivityDefinitionTestMixin


class ActivityDefinitionConverterTestCase(ActivityDefinitionTestMixin):
    __TEST_ACTIVITY_DEFINITION_JSON_PATH = "/test/test_activity_definition.json"

    @classmethod
    def setUpClass(cls):
        super(ActivityDefinitionConverterTestCase, cls).setUpClass()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        cls.__TEST_ACTIVITY_DEFINITION_JSON_TEXT__ = open(dir_path + cls.__TEST_ACTIVITY_DEFINITION_JSON_PATH).read()

    def setUp(self):
        super(ActivityDefinitionConverterTestCase, self).setUp()

    def test_to_fhir_obj(self):
        imis_service = self.create_test_imis_instance()
        fhir_activity_definition = ActivityDefinitionConverter.to_fhir_obj(imis_service)
        self.verify_fhir_instance(fhir_activity_definition)

    def test_to_imis_obj(self):
        fhir_activity_definition = self.create_test_fhir_instance()
        imis_service = ActivityDefinitionConverter.to_imis_obj(fhir_activity_definition.dict(), None)
        self.verify_imis_instance(imis_service)

    def test_create_object_from_json(self):
        dict_activity_definition = json.loads(
            ActivityDefinitionConverterTestCase.__TEST_ACTIVITY_DEFINITION_JSON_TEXT__)
        fhir_activity_definition = ActivityDefinition(**dict_activity_definition)
        self.verify_fhir_instance(fhir_activity_definition)
