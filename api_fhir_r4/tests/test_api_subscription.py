from rest_framework.test import APITestCase
from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiCreateTestMixin, FhirApiReadTestMixin, \
    FhirApiDeleteTestMixin, FhirApiUpdateTestMixin
from api_fhir_r4.tests.mixin.SubscriptionTestMixin import SubscriptionTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin


class SubscriptionAPITests(GenericFhirAPITestMixin, APITestCase, LogInMixin, FhirApiCreateTestMixin,
                           FhirApiReadTestMixin, FhirApiDeleteTestMixin, FhirApiUpdateTestMixin,
                           SubscriptionTestMixin):
    base_url = GeneralConfiguration.get_base_url() + 'Subscription/'
    _test_json_path = "/test/test_subscription.json"
    _updated_endpoint = 'https://modifiedendpoint.com'

    def update_resource(self, data):
        data['channel']['endpoint'] = self._updated_endpoint

    def verify_updated_obj(self, obj):
        self.assertEqual(obj.channel.endpoint, self._updated_endpoint)

    def setUp(self):
        super(SubscriptionAPITests, self).setUp()
        user = self.get_or_create_user_api()
        subscription = self.create_test_imis_instance()
        subscription.id = None
        subscription.save(username=user.username)

    def get_id_for_created_resource(self, response):
        return response.data['id']
