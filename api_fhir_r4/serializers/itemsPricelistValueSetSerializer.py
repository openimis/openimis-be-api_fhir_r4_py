from api_fhir_r4.serializers.valueSetSerializer import ValueSetSerializer
from medical_pricelist.models import ItemsPricelistDetail


class ItemsPricelistValueSetSerializer(ValueSetSerializer):

    def __init__(self, *args, **kwargs):
        # Get pricelist details with related item data
        queryset = ItemsPricelistDetail.objects.select_related('item', 'items_pricelist')

        # Build data for each item with properties
        data = []
        for detail in queryset:
            item_data = {
                'code': detail.item.code,
                'display': detail.item.name,
                'price': str(detail.price_overrule) if detail.price_overrule else '0.00',
                'pricelist_name': detail.items_pricelist.name,
                'pricelist_date': str(detail.items_pricelist.pricelist_date),
            }
            data.append(item_data)

        kwargs['data'] = data
        kwargs['code_field'] = 'code'
        kwargs['display_field'] = 'display'
        kwargs['id'] = 'items-pricelist'
        kwargs['name'] = 'ItemsPricelistVS'
        kwargs['title'] = 'Medical Items Pricelist'
        kwargs['description'] = 'Medical items with pricing information from openIMIS price lists.'
        # codesystem_url will be set in to_representation
        kwargs['properties'] = ['price', 'pricelist_name', 'pricelist_date']

        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        # Set the codesystem URL dynamically
        request = self.context.get('request')
        if request:
            base_url = request.build_absolute_uri().rstrip('/ValueSet/items-pricelist')
            self.model['codesystem_url'] = f"{base_url}/CodeSystem/medical-item"
            self.model['url'] = request.build_absolute_uri()

        return super().to_representation(obj)
