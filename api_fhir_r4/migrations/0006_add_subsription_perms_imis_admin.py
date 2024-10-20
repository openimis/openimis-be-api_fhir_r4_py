# Generated by Django 3.2.16 on 2023-05-04 11:56
import logging

from django.db import migrations
from core.utils import insert_role_right_for_system

logger = logging.getLogger(__name__)

IMIS_ADMIN_ROLE_IS_SYSTEM = 64
SUB_SEARCH_ROLE_RIGHT_ID = 158001
SUB_CREATE_ROLE_RIGHT_ID = 158002
SUB_UPDATE_ROLE_RIGHT_ID = 158003
SUB_DELETE_ROLE_RIGHT_ID = 158004


def add_rights(apps, schema_editor):
    """
    Add subscription CRUD permission to the IMIS Administrator.
    """
    insert_role_right_for_system(IMIS_ADMIN_ROLE_IS_SYSTEM, SUB_SEARCH_ROLE_RIGHT_ID, apps)
    insert_role_right_for_system(IMIS_ADMIN_ROLE_IS_SYSTEM, SUB_CREATE_ROLE_RIGHT_ID, apps)
    insert_role_right_for_system(IMIS_ADMIN_ROLE_IS_SYSTEM, SUB_UPDATE_ROLE_RIGHT_ID, apps)
    insert_role_right_for_system(IMIS_ADMIN_ROLE_IS_SYSTEM, SUB_DELETE_ROLE_RIGHT_ID, apps)


def remove_rights(apps, schema_editor):
    """
    Remove subscription CRUD permissions to the IMIS Administrator.
    """
    RoleRight = apps.get_model('core', 'RoleRight')

    RoleRight.objects.filter(
        role__is_system=IMIS_ADMIN_ROLE_IS_SYSTEM,
        right_id__in=[SUB_CREATE_ROLE_RIGHT_ID, SUB_DELETE_ROLE_RIGHT_ID,
                      SUB_SEARCH_ROLE_RIGHT_ID, SUB_UPDATE_ROLE_RIGHT_ID],
        validity_to__isnull=True
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api_fhir_r4', '0005_auto_20221012_0818'),
        ('core', '0015_missing_roles')
    ]

    operations = [
        migrations.RunPython(add_rights, remove_rights),
    ]
