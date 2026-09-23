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
        Les droits régissant une action sur cette entité, pour REST et FHIR.

        Ne redéclare rien : la table des droits est `api_fhir_r4.apps.DJANGO_PERMS`, par
        entité puis par action, et `configured_perms` y lit la valeur *configurée* -
        celle que ModuleConfiguration a pu surcharger - et non le défaut déclaré. Ce
        modèle n'est que le point d'accès, comme `get_queryset` l'est pour les lignes.

        La lecture se fait ici, à l'appel : les attributs `_perms` ne valent leur valeur
        qu'après `ready()`, et un instantané pris à l'import capturerait le placeholder,
        donc une liste vide - que `has_perms` accorde à tout le monde.
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
    # Sous-ressource : une notification n'existe que pour une souscription, et c'est la
    # seule clé étrangère du modèle - il n'y a donc pas d'ambiguïté sur le propriétaire.
    # Elle n'a pas de droits à elle : `model_rights` remonte à Subscription.get_rights.
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
