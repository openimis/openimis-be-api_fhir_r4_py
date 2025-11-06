from api_fhir_r4.converters.contractConverter import ContractConverter
from api_fhir_r4.serializers.baseSerializer import BaseFHIRSerializer
from contribution.services import update_or_create_premium
from policy.services import PolicyService
from policy.models import Policy
import copy
from api_fhir_r4.exceptions import FHIRException


class ContractSerializer(BaseFHIRSerializer):
    fhirConverter = ContractConverter

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        family = validated_data.get("family_id")
        insurees = validated_data.pop("insurees")
        premiums = validated_data.pop("contributions")

        if (
            Policy.objects.filter(family_id=family)
            .filter(
                start_date__range=[
                    validated_data.get("effective_date"),
                    validated_data.get("expiry_date"),
                ]
            )
            .count()
            > 0
        ):
            raise FHIRException("Contract exists for this patient")

        copied_data = copy.deepcopy(validated_data)
        if "_state" in copied_data:
            del copied_data["_state"]
        # TODO should we implement a way to create a resource with a given uuid
        del copied_data["uuid"]

        # Add insurees to the data for PolicyService
        if insurees:
            copied_data["members_uuid"] = insurees

        new_policy = PolicyService(user).update_or_create(copied_data, user)
        # create contributions related to newly created policy
        if premiums:
            for premium in premiums:
                premium.policy = new_policy
                premium = update_or_create_premium(premium, user)
                new_policy = premium.policy

        return new_policy

    def update(self, instance, validated_data):
        instance.save()
        return instance
