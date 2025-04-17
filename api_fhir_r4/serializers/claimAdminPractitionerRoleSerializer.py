from core.models.user import ClaimAdmin
from django.utils.translation import gettext

from api_fhir_r4.converters import ClaimAdminPractitionerRoleConverter
from api_fhir_r4.exceptions import FHIRRequestProcessException
from api_fhir_r4.serializers import BaseFHIRSerializer


class ClaimAdminPractitionerRoleSerializer(BaseFHIRSerializer):

    fhirConverter = ClaimAdminPractitionerRoleConverter

    def create(self, validated_data):
        claim_admin_id = validated_data.get('id')
        claim_admin = None
        if claim_admin_id:
            claim_admin = ClaimAdmin.objects.get(pk=claim_admin_id)
        if not claim_admin:
            raise FHIRRequestProcessException([gettext('Missing Practitioner for id {}').format(claim_admin_id)])
        claim_admin.health_facility_id = validated_data.get('health_facility_id', claim_admin.health_facility_id)
        claim_admin.save()
        return claim_admin

    def update(self, instance, validated_data):
        instance.health_facility_id = validated_data.get('health_facility_id', instance.health_facility_id)
        instance.audit_user_id = self.get_audit_user_id()
        instance.save()
        return instance
