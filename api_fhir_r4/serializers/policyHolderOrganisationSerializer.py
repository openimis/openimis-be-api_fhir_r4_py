import copy
from policyholder.models import PolicyHolder
from api_fhir_r4.converters import PolicyHolderOrganisationConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer


class PolicyHolderOrganisationSerializer(BaseFHIRSerializer):
    fhirConverter = PolicyHolderOrganisationConverter

    def create(self, validated_data):
        if PolicyHolder.objects.filter(code=validated_data['code']).count() > 0:
            raise FHIRException('Exists Organization with following code `{}`'.format(validated_data['code']))
        validated_data.pop('_original_state')
        validated_data.pop('_state', None)
        request = self.context.get('request', None)
        if request:
            validated_data['user_created_id']=request.user.id
            validated_data['user_updated_id']=request.user.id
        obj=PolicyHolder(**validated_data)
        obj.save()
        return obj

    def update(self, instance, validated_data):
        request = self.context.get('request', None)
        if request:
            validated_data['user_updated_id'] = request.user.id
        instance.legal_form = validated_data.get('legal_form', instance.legal_form)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.email = validated_data.get('email', instance.email)
        instance.fax = validated_data.get('fax', instance.fax)
        instance.trade_name = validated_data.get('trade_name', instance.trade_name)
        instance.address = validated_data.get('address', instance.address)
        instance.bank_account = validated_data.get('bank_account', instance.address)
        instance.accountancy_account = validated_data.get('accountancy_account', instance.accountancy_account)
        instance.user_updated_id = validated_data.get('user_updated_id', instance.user_updated_id)
        instance.save()
        return instance
