"""
Who may subscribe to a FHIR resource, and who may be notified of a given instance.

A subscription is a standing read: every change to a matching instance is pushed to
the subscriber's endpoint. So the subscriber needs what a read would need, checked
with the same definitions as every other API (OP-3351, CVE-2026-82494):

* the read right of the model, as the model declares it (`Model.get_rights("query")`,
  through `core.rights_scope`), so a right overridden in ModuleConfiguration is
  honoured;
* for a notification, that instance inside the subscriber's row scope
  (`Model.get_queryset`).
"""
import logging

from django.apps import apps

from core.rights_scope import has_model_right, model_rights

logger = logging.getLogger(__name__)

# FHIR resource named in a subscription's criteria -> the openIMIS models it is built
# from. The keys are lower-cased; `signals.py` emits "Patient", "Claim", "Invoice"
# (bills and invoices) and "Organisation" (health facilities).
SUBSCRIBABLE_RESOURCES = {
    "patient": ("insuree.Insuree",),
    "claim": ("claim.Claim",),
    "invoice": ("invoice.Invoice", "invoice.Bill"),
    "organisation": ("location.HealthFacility",),
}


def _fallback_read_rights():
    """
    The FHIR read rights of the models that do not declare `get_rights` yet.

    Used only while such a model has no declaration, so that subscribing to it stays
    exactly as open as reading it through the FHIR API - never more. Once the model
    declares its rights, `model_rights` answers and this is not consulted.
    """
    from api_fhir_r4.permissions import FHIRApiHealthServicePermissions

    return {
        "location.healthfacility": FHIRApiHealthServicePermissions.permissions_get,
    }


def _label(model):
    return f"{model._meta.app_label}.{model._meta.model_name}"


def resource_models(resource_name):
    """The installed models behind a FHIR resource name; empty when unknown."""
    models = []
    for label in SUBSCRIBABLE_RESOURCES.get((resource_name or "").lower(), ()):
        try:
            models.append(apps.get_model(label))
        except LookupError:
            logger.debug("subscription resource model %s is not installed", label)
    return models


def has_read_right(user, model):
    """Whether `user` holds the read right of `model`. Fails closed."""
    if model_rights(model, "query") is not None:
        return has_model_right(user, model, "query")
    fallback = _fallback_read_rights().get(_label(model))
    if fallback is None:
        logger.error(
            "no read right declared for %s - refusing the subscription", _label(model)
        )
        return False
    return user.has_perms(list(fallback))


def can_subscribe(user, resource_name):
    """
    Whether `user` may subscribe to `resource_name`.

    A resource built from several models (Invoice: invoices and bills) needs the read
    right of at least one of them: each notification is still checked against the
    model of the instance that changed (`may_be_notified`).
    """
    return any(has_read_right(user, model) for model in resource_models(resource_name))


def notification_refusal(owner, instance):
    """
    Why `owner` may not be notified of `instance`, or None when they may.

    Checked at notification time, not only at subscription time: the owner may have
    been deleted, lost the right, or the instance may sit outside their scope.
    """
    if owner is None or not owner.is_active:
        return "subscription owner is missing or inactive"
    model = type(instance)
    if not has_read_right(owner, model):
        return f"subscription owner lacks the read right on {_label(model)}"
    in_scope = model.get_queryset(model.objects.filter(pk=instance.pk), owner)
    if not in_scope.exists():
        return "resource is outside the subscription owner's scope"
    return None
