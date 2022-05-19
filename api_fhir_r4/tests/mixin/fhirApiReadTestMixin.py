from rest_framework import status


class FhirApiReadTestMixin(object):

    @property
    def base_url(self):
        raise NotImplementedError()

    def login(self):
        raise NotImplementedError()

    def test_get_bad_authorization(self):
        response = self.client.get(self.base_url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_should_return_200(self):
        self.login()
        response = self.client.get(self.base_url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
