from rest_framework import status


class FhirApiCreateTestMixin(object):

    @property
    def base_url(self):
        raise NotImplementedError()

    @property
    def _test_request_data(self):
        raise NotImplementedError()

    def login(self):
        raise NotImplementedError()

    def test_post_should_create_correctly(self):
        self.login()
        self.create_dependencies()
        response = self.client.post(self.base_url, data=self._test_request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.content)

    def create_dependencies(self):
        pass
