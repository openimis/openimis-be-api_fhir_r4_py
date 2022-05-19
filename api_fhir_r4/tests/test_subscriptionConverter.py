from fhir.resources.subscription import Subscription

from api_fhir_r4.subscriptions import SubscriptionConverter
from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin
from api_fhir_r4.tests.mixin.SubscriptionTestMixin import SubscriptionTestMixin
from api_fhir_r4.utils import TimeUtils


class SubscriptionConverterTestCase(SubscriptionTestMixin,
                                    ConvertToImisTestMixin,
                                    ConvertToFhirTestMixin,
                                    ConvertJsonToFhirTestMixin):
    converter = SubscriptionConverter
    fhir_resource = Subscription
    json_repr = 'test/test_subscription.json'

    def _load_json_repr(self):
        json_repr = super(SubscriptionConverterTestCase, self)._load_json_repr()
        json_repr['end'] = TimeUtils.str_iso_to_date(json_repr['end'])
        return json_repr


