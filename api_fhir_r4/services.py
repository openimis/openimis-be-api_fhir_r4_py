from api_fhir_r4.models import Subscription
from api_fhir_r4.validation import SubscriptionValidation
from core.services import BaseService


class SubscriptionService(BaseService):
    OBJECT_TYPE = Subscription

    def __init__(self, user, validation_class=SubscriptionValidation):
        super().__init__(user, validation_class)
