from api_fhir_r4.converters import ValueSetConverter
from api_fhir_r4.serializers.baseSerializer import BaseFHIRSerializer


class ValueSetSerializer(BaseFHIRSerializer):
    fhirConverter = ValueSetConverter

    def __init__(self, *args, **kwargs):
        self.valueSetFields = [
            "code_field",
            "display_field",
            "id",
            "name",
            "title",
            "description",
            "url",
            "codesystem_url",
            "properties",
        ]
        self.model = {}
        if "user" in kwargs:
            user = kwargs.pop("user")
        for field in self.valueSetFields:
            self.model[field] = kwargs.pop(field, None)
        if "data" in kwargs:
            self.model["data"] = kwargs.pop("data")
        else:
            self.model["data"] = {}

        super().__init__(*args, user=user, **kwargs)

    def to_representation(self, obj):
        return ValueSetConverter.to_fhir_obj(self.model, self.reference_type).dict()
