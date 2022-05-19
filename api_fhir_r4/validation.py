from api_fhir_r4.models import Subscription
from core.validation import BaseModelValidation


class SubscriptionValidation(BaseModelValidation):
    OBJECT_TYPE = Subscription

    @classmethod
    def validate_create(cls, user, **data):
        super().validate_create(user, **data)

    @classmethod
    def validate_update(cls, user, **data):
        super().validate_update(user, **data)

    @classmethod
    def validate_delete(cls, user, **data):
        super().validate_delete(user, **data)
