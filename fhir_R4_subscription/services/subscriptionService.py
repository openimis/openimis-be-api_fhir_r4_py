from ..models import Subscription
from ..validation import SubscriptionValidation
from core.services import BaseService


class SubscriptionService(BaseService):
    OBJECT_TYPE = Subscription

    def __init__(self, user, validation_class=SubscriptionValidation):
        super().__init__(user, validation_class)
