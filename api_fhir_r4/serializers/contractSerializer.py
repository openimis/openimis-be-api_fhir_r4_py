from api_fhir_r4.converters.contractConverter import ContractConverter
from api_fhir_r4.serializers import BaseFHIRSerializer
from contribution.gql_mutations import update_or_create_premium
from policy.services import PolicyService
from policy.models import Policy
import copy
from api_fhir_r4.exceptions import FHIRException


class ContractSerializer(BaseFHIRSerializer):
    fhirConverter = ContractConverter

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        family = validated_data.get('family_id')
        insurees = validated_data.pop('insurees')
        premiums = validated_data.pop('contributions')

        if Policy.objects.filter(family_id=family).filter(start_date__range=[validated_data.get('effective_date'),validated_data.get('expiry_date')]).count() > 0:
            raise FHIRException('Contract exists for this patient')

        copied_data = copy.deepcopy(validated_data)
        del copied_data['_state']

        new_policy = PolicyService(user).update_or_create(copied_data, user)
        # create contributions related to newly created policy
        if premiums:
            for premium in premiums:
                premium = premium.__dict__
                del premium['_state']
                premium['policy_uuid'] = new_policy.uuid
                premium['policy_id'] = new_policy.id
                premium['audit_user_id'] = copied_data['audit_user_id']
                premium = update_or_create_premium(premium, user)
                new_policy = premium.policy

        return new_policy
    
    def update(self, instance, validated_data):
        instance.save()
        return instance
