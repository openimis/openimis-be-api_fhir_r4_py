from functools import lru_cache

from claim.models import Claim
from core.models import User

from api_fhir_r4.converters import ClaimResponseConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


class ClaimResponseSerializer(BaseFHIRSerializer):

    fhirConverter = ClaimResponseConverter

    UPDATABLE_FIELDS = ['status', 'rejection_reason', 'date_from', 'date_to', 'feedback', 'visit_type',
                        'review_status', 'health_facility', 'adjustment', 'icd', 'icd_1', 'icd_2', 'icd_3', 'icd_4']

    def update(self, instance: Claim, validated_data):
        self._assign_values_if_available(instance, validated_data)
        self._save_claim_serviced_items(instance, validated_data)
        self._assign_audit_user_id(instance, self.get_audit_user_id())
        instance.save()
        return instance

    def _assign_values_if_available(self, instance, validated_data, fields=None):
        if fields is None:
            fields = self.UPDATABLE_FIELDS

        for next_field in fields:
            new_value = validated_data.get(next_field, None)
            if new_value:
                setattr(instance, next_field, new_value)

    def _save_claim_serviced_items(self, instance, validated_data):
        items = validated_data.get('claim_items', [])
        services = validated_data.get('claim_services', [])
        audit_user_id = self.get_audit_user_id()

        for serviced in items+services:
            serviced.claim = instance
            self._assign_audit_user_id(serviced, audit_user_id)
            serviced.save()

    def _assign_audit_user_id(self, model, audit_user_id):
        if isinstance(model.audit_user_id, int) and not isinstance(audit_user_id, int):
            # In case if model use Id instead of uuid
            audit_user = self._get_audit_user(audit_user_id)
            model.audit_user_id = audit_user.id
        else:
            model.audit_user_id = audit_user_id

    @lru_cache(maxsize=None)
    def _get_audit_user(self, audit_user_uuid: str) -> User:
        return User.objects.get(uuid=audit_user_uuid)
