import logging

from django.db import migrations
from django.db.models import Q

logger = logging.getLogger(__name__)


def update_subscription_criteria(apps, schema_editor):
    resource_type_map = {
        'Invoice': 'Invoice',
        'Bill': 'Invoice',
        'Patient': 'Patient',
        'Organisation': 'Organisation'
    }

    subscription_model = apps.get_model('api_fhir_r4', 'Subscription')
    entries_to_update = subscription_model.objects\
        .filter(Q(criteria__has_key='resource_type')  & ~Q(criteria__has_key='resource'))
    for subscription in entries_to_update:
        resource = subscription.criteria.pop('resource_type')
        if resource in resource_type_map:
            subscription.criteria['resource'] = resource_type_map[resource]
            subscription.save()
        else:
            logger.warning(f'Subscription of unexpected type - {resource}')


class Migration(migrations.Migration):

    dependencies = [
        ('api_fhir_r4', '0003_auto_20220313_1634'),
    ]

    operations = [
        migrations.RunPython(update_subscription_criteria, migrations.RunPython.noop)
    ]
