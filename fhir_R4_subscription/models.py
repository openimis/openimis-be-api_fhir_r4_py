import uuid

from django.db import models
from django.db.models import F
from django.utils.translation import gettext as _
from django_cryptography.fields import encrypt

from core.datetimes import ad_datetime
from core.fields import DateTimeField
from core.models import HistoryBusinessModel


class Subscription(HistoryBusinessModel):
    class SubscriptionStatus(models.IntegerChoices):
        INACTIVE = 0, _('inactive')
        ACTIVE = 1, _('active')

    class SubscriptionChannel(models.IntegerChoices):
        REST_HOOK = 0, _("rest-hook")

    status = models.SmallIntegerField(db_column='Status', null=False, choices=SubscriptionStatus.choices)
    channel = models.SmallIntegerField(db_column='Channel', null=False, choices=SubscriptionChannel.choices)
    endpoint = models.CharField(db_column='Endpoint', max_length=255, null=False)
    headers = encrypt(models.TextField(db_column='Headers', max_length=255, blank=True, null=True))
    criteria = models.JSONField(db_column='Criteria', blank=True, null=True)
    expiring = models.DateTimeField(db_column='Expiring', null=False)
    
    # Override user fields to avoid conflicts with api_fhir_r4 module
    user_created = models.ForeignKey('core.User', on_delete=models.DO_NOTHING, related_name='fhir_r4_subscription_user_created', null=True, blank=True)
    user_updated = models.ForeignKey('core.User', on_delete=models.DO_NOTHING, related_name='fhir_r4_subscription_user_updated', null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'tblFhirR4Subscription'


class SubscriptionNotificationResultManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(uuid=F('id'))

    def subscriber_notifications(self, subscriber: Subscription):
        return self.get_queryset().filter(subscription__id=subscriber.id)


class SubscriptionNotificationResult(models.Model):
    id = models.UUIDField(primary_key=True, db_column="UUID", default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name='fhir_r4_notifications_sent', null=False)
    notified_successfully = models.BooleanField(blank=False, null=False)
    notification_time = DateTimeField(db_column='Expiring', null=False, default=ad_datetime.AdDatetime.now)
    error = models.TextField(blank=True, null=True, default=None)

    objects = SubscriptionNotificationResultManager()

    class Meta:
        managed = True
        db_table = 'tblFhirR4SubscriptionNotificationResult'
