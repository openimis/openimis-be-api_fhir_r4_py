from api_fhir_r4.serializers.valueSetSerializer import ValueSetSerializer
from medical_pricelist.models import ServicesPricelistDetail


class ServicesPricelistValueSetSerializer(ValueSetSerializer):

    def __init__(self, *args, **kwargs):
        # Get pricelist details with related service data
        queryset = ServicesPricelistDetail.objects.select_related('service', 'services_pricelist')

        # Build data for each service with properties
        data = []
        for detail in queryset:
            service_data = {
                'code': detail.service.code,
                'display': detail.service.name,
                'price': str(detail.price_overrule) if detail.price_overrule else '0.00',
                'pricelist_name': detail.services_pricelist.name,
                'pricelist_date': str(detail.services_pricelist.pricelist_date),
            }
            data.append(service_data)

        kwargs['data'] = data
        kwargs['code_field'] = 'code'
        kwargs['display_field'] = 'display'
        kwargs['id'] = 'services-pricelist'
        kwargs['name'] = 'ServicesPricelistVS'
        kwargs['title'] = 'Medical Services Pricelist'
        kwargs['description'] = 'Medical services with pricing information from openIMIS price lists.'
        # codesystem_url will be set in to_representation
        kwargs['properties'] = ['price', 'pricelist_name', 'pricelist_date']

        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        # Set the codesystem URL dynamically
        request = self.context.get('request')
        if request:
            base_url = request.build_absolute_uri().rstrip('/ValueSet/services-pricelist')
            self.model['codesystem_url'] = f"{base_url}/CodeSystem/medical-service"
            self.model['url'] = request.build_absolute_uri()

        return super().to_representation(obj)
