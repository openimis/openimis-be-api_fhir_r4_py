from fhir.resources.R4B.operationoutcome import OperationOutcome
from rest_framework import status

from api_fhir_r4.configurations import R4IssueTypeConfig


class FhirApiDeleteTestMixin(object):

    @property
    def base_url(self):
        raise NotImplementedError()

    @property
    def _test_request_data(self):
        raise NotImplementedError()

    def get_id_for_created_resource(self, response):
        raise NotImplementedError()

    def get_fhir_obj_from_json_response(self, response):
        raise NotImplementedError()

    def login(self):
        raise NotImplementedError()

    def test_delete_should_remove_correctly(self):
        self.login()
        # create
        self.create_dependencies()
        response = self.client.post(self.base_url, data=self._test_request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resource_id = self.get_id_for_created_resource(response)
        # verify if exist
        response = self.client.get(self.base_url + resource_id + "/", data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.content)

        response = self.client.delete(self.base_url + resource_id + "/", data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(not response.content)

        # verify if deleted
        response = self.client.get(self.base_url + resource_id + "/", data=None, format='json')
        self.verify_deleted_response(response)

    def create_dependencies(self):
        pass

    def verify_deleted_response(self, response):
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        #FIXME detail is sent on the test iso OO
        # operation_outcome = self.get_fhir_obj_from_json_response(response)
        #self.assertTrue(isinstance(operation_outcome, OperationOutcome))
        #self.assertEqual(R4IssueTypeConfig.get_fhir_code_for_not_found(), operation_outcome.issue[0].code)
