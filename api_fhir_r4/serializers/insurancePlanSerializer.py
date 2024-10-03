import copy

from product.models import Product
from api_fhir_r4.converters import InsurancePlanConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer


class InsurancePlanSerializer(BaseFHIRSerializer):
    fhirConverter = InsurancePlanConverter

    def create(self, validated_data):
        code = validated_data.get('code')
        if Product.objects.filter(code=code).count() > 0:
            raise FHIRException('Exists product with following code `{}`'.format(code))
        copied_data = copy.deepcopy(validated_data)
        if '_state' in copied_data:
            del copied_data['_state']
        # TODO services in product hasn't been developed yet.
        return Product.objects.create(**copied_data)

    def update(self, instance, validated_data):
        instance.code = validated_data.get('code', instance.code)
        instance.name = validated_data.get('name', instance.name)
        instance.date_from = validated_data.get('date_from', instance.date_from)
        instance.date_to = validated_data.get('date_to', instance.date_from)
        instance.location = validated_data.get('location', instance.location)
        instance.member_count = validated_data.get('member_count', instance.member_count)
        instance.insurance_period = validated_data.get('insurance_period', instance.insurance_period)
        instance.lump_sum = validated_data.get('lump_sum', instance.lump_sum)
        instance.threshold = validated_data.get('threshold', instance.threshold)
        instance.premium_adult = validated_data.get('premium_adult', instance.premium_adult)
        instance.premium_child = validated_data.get('premium_child', instance.premium_child)
        instance.registration_lump_sum = validated_data.get('registration_lump_sum', instance.registration_lump_sum)
        instance.registration_fee = validated_data.get('registration_fee', instance.registration_fee)
        instance.general_assembly_lump_sum = validated_data.get(
            'general_assembly_lump_sum', instance.general_assembly_lump_sum
        )
        instance.general_assembly_fee = validated_data.get('general_assembly_fee', instance.general_assembly_fee)
        instance.conversion_product = validated_data.get('conversion_product', instance.conversion_product)
        instance.max_installments = validated_data.get('max_installments', instance.max_installments)
        instance.grace_period_enrolment = validated_data.get('grace_period_enrolment', instance.grace_period_enrolment)
        instance.audit_user_id = self.get_audit_user_id()
        instance.save()
        return instance
