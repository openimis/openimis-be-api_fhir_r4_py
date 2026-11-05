import uuid

from django.db import models
from django.db.models import F
from django.utils.translation import gettext as _
from django_cryptography.fields import encrypt

from core.datetimes import ad_datetime
from core.fields import DateTimeField
from core.models import HistoryBusinessModel


class Subscription(HistoryBusinessModel):
    @classmethod
    def get_rights(cls, action):
        """
        The rights governing an action on this entity, for REST and FHIR.

        Redeclares nothing: the rights table is `api_fhir_r4.apps.DJANGO_PERMS`, by
        entity then by action, and `configured_perms` reads the *configured* value
        there - the one ModuleConfiguration may have overridden - and not the declared
        default. This model is only the access point, as `get_queryset` is for the
        rows.

        The read happens here, at call time: the `_perms` attributes only hold their
        value after `ready()`, and a snapshot taken at import would capture the
        placeholder, hence an empty list - which `has_perms` grants to everybody.
        """
        from api_fhir_r4.apps import configured_perms

        return configured_perms("subscription", action)

    class SubscriptionStatus(models.IntegerChoices):
        INACTIVE = 0, _("inactive")
        ACTIVE = 1, _("active")

    class SubscriptionChannel(models.IntegerChoices):
        REST_HOOK = 1, _("rest-hook")

    status = models.SmallIntegerField(
        db_column="Status", null=False, choices=SubscriptionStatus.choices
    )
    channel = models.SmallIntegerField(
        db_column="Channel", null=False, choices=SubscriptionChannel.choices
    )
    endpoint = models.CharField(db_column="Endpoint", max_length=255, null=False)
    headers = encrypt(
        models.TextField(db_column="Headers", max_length=255, blank=True, null=True)
    )
    criteria = models.JSONField(db_column="Criteria", blank=True, null=True)
    expiring = models.DateTimeField(db_column="Expiring", null=False)

    class Meta:
        managed = True
        db_table = "tblSubscription"


class SubscriptionNotificationResultManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(uuid=F("id"))

    def subscriber_notifications(self, subscriber: Subscription):
        return self.get_queryset().filter(subscription__id=subscriber.id)


class SubscriptionNotificationResult(models.Model):
    # A sub-resource: a notification exists only for a subscription, and that is the
    # model's only foreign key - so there is no ambiguity about the owner. It has no
    # rights of its own: `model_rights` walks up to Subscription.get_rights.
    scope_parent = "subscription"

    id = models.UUIDField(
        primary_key=True, db_column="UUID", default=uuid.uuid4, editable=False
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="notifications_sent",
        null=False,
    )
    notified_successfully = models.BooleanField(blank=False, null=False)
    notification_time = DateTimeField(
        db_column="Expiring", null=False, default=ad_datetime.AdDatetime.now
    )
    error = models.TextField(blank=True, null=True, default=None)

    objects = SubscriptionNotificationResultManager()

    class Meta:
        managed = True
        app_label = 'api_fhir_r4'
        db_table = "tblSubscriptionNotificationResult"
