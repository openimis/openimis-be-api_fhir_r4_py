from django.test import TestCase

from api_fhir_r4.models import Subscription
from api_fhir_r4.services import SubscriptionService
from api_fhir_r4.utils import TimeUtils
from core.models import User


class SubscriptionServiceTest(TestCase):
    user = None
    service = None
    create_payload = {
        'status': 1,
        'channel': 0,
        'expiring': TimeUtils.str_iso_to_date('2021-01-01T01:02:03+01:00'),
        'endpoint': 'https://subscriptiontest.com/test',
        'headers': 'Authentication=Bearer 12351231',
        'criteria': {
            'resource_type': 'Patient',
            'chfid__startswith': '1',
        },
    }

    update_payload = {
        'status': 0
    }

    @classmethod
    def setUpTestData(cls):
        if not User.objects.filter(username='admin_sub_service').exists():
            User.objects.create_superuser(username='admin_sub_service', password='S\/pe®Pąßw0rd™')
        cls.user = User.objects.filter(username='admin_sub_service').first()
        cls.service = SubscriptionService(cls.user)

    def test_create(self):
        result = self.service.create(self.create_payload)
        self.assertIsInstance(result, dict)
        self.assertTrue(result['success'])
        self.assertEqual('Ok'.lower(), result['message'].lower())
        created_id = result['data']['id']
        self.assertTrue(created_id)
        queryset = Subscription.objects.filter(id=created_id)
        self.assertEqual(queryset.count(), 1)

    def test_update(self):
        result_create = self.service.create(self.create_payload)
        created_id = result_create['data']['id']
        update_payload = {**self.update_payload, **{'id': created_id}}
        result = self.service.update(update_payload)
        self.assertIsInstance(result, dict)
        self.assertTrue(result['success'])
        self.assertEqual('Ok'.lower(), result['message'].lower())
        changed_fields = {key: result['data'][key] for key in result['data'] if key in update_payload}
        self.assertDictEqual(update_payload, changed_fields)
        queryset = Subscription.objects.filter(id=created_id)
        self.assertEqual(queryset.count(), 1)

    def test_delete(self):
        result_create = self.service.create(self.create_payload)
        created_id = result_create['data']['id']
        delete_payload = {'id': created_id}
        result = self.service.delete(delete_payload)
        self.assertTrue(result['success'])
        self.assertEqual('Ok'.lower(), result['message'].lower())
        queryset = Subscription.objects.filter(id=created_id, is_deleted=True)
        self.assertEqual(queryset.count(), 1)
        queryset = Subscription.objects.filter(id=created_id, is_deleted=False)
        self.assertEqual(queryset.count(), 0)
