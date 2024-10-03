from django.contrib.contenttypes.models import ContentType
from api_fhir_r4.converters import CodeSystemConverter
from api_fhir_r4.serializers import BaseFHIRSerializer


class CodeSystemSerializer(BaseFHIRSerializer):
    fhirConverter = CodeSystemConverter
    codeSystemFields = ['code_field', 'display_field', 'id', 'name', 'title', 'description', 'url']

    def __init__(self, *args, **kwargs):
        self.model = {}
        if 'user' in kwargs:
            user = kwargs.pop('user')
        for field in self.codeSystemFields:
            self.model[field] = kwargs.pop(field, None)
        if 'data' in kwargs:
            self.model['data'] = kwargs.pop('data')
        elif 'model_name' in kwargs:
            content_type = ContentType.objects.get(model__iexact=kwargs.pop('model_name'))
            model_class = content_type.model_class()
            self.model['data'] = model_class.objects.all()
        else:
            self.model['data'] = {}

        super().__init__(*args, user=user, **kwargs)

    def to_representation(self, obj):
        return CodeSystemConverter.to_fhir_obj(self.model, self.reference_type).dict()
