from api_fhir_r4.converters import BaseFHIRConverter
from fhir.resources.R4B.valueset import ValueSet, ValueSetCompose, ValueSetComposeInclude, ValueSetExpansion, ValueSetExpansionContains
from api_fhir_r4.utils import FhirUtils


class ValueSetConverter(BaseFHIRConverter):

    @classmethod
    def to_imis_obj(cls, data, audit_user_id):
        raise NotImplementedError("`toImisObj()` not implemented.")  # pragma: no cover

    @classmethod
    def get_fhir_code_identifier_type(cls):
        raise NotImplementedError(
            "`get_fhir_code_identifier_type()` not implemented."
        )  # pragma: no cover

    @classmethod
    def to_fhir_obj(cls, obj, reference_type):
        fhir_value_set = {}
        cls.build_fhir_value_set_status(fhir_value_set)
        cls.build_fhir_value_set_compose(fhir_value_set, obj)
        cls.build_fhir_value_set_expansion(fhir_value_set, obj)
        fhir_value_set = ValueSet(**fhir_value_set)
        cls.build_fhir_id(fhir_value_set, obj)
        cls.build_fhir_url(fhir_value_set, obj)
        cls.build_fhir_value_set_name(fhir_value_set, obj)
        cls.build_fhir_value_set_title(fhir_value_set, obj)
        cls.build_fhir_value_set_date(fhir_value_set)
        cls.build_fhir_value_set_description(fhir_value_set, obj)
        return fhir_value_set

    @classmethod
    def build_fhir_id(cls, fhir_value_set, obj):
        fhir_value_set.id = obj["id"]

    @classmethod
    def build_fhir_url(cls, fhir_value_set, obj):
        fhir_value_set.url = obj["url"]

    @classmethod
    def build_fhir_value_set_name(cls, fhir_value_set, obj):
        fhir_value_set.name = obj["name"]

    @classmethod
    def build_fhir_value_set_title(cls, fhir_value_set, obj):
        fhir_value_set.title = obj["title"]

    @classmethod
    def build_fhir_value_set_date(cls, fhir_value_set):
        from core.utils import TimeUtils

        fhir_value_set.date = TimeUtils.now()

    @classmethod
    def build_fhir_value_set_description(cls, fhir_value_set, obj):
        fhir_value_set.description = obj["description"]

    @classmethod
    def build_fhir_value_set_status(cls, fhir_value_set):
        fhir_value_set["status"] = "active"

    @classmethod
    def build_fhir_value_set_compose(cls, fhir_value_set, obj):
        compose = ValueSetCompose.construct()
        compose.include = []

        include = ValueSetComposeInclude.construct()
        include.system = obj["codesystem_url"]
        compose.include.append(include)

        fhir_value_set.compose = compose

    @classmethod
    def build_fhir_value_set_expansion(cls, fhir_value_set, obj):
        expansion = ValueSetExpansion.construct()
        expansion.contains = []

        for item in obj["data"]:
            contains = ValueSetExpansionContains.construct()
            contains.code = FhirUtils.get_attr(item, obj["code_field"])
            contains.display = FhirUtils.get_attr(item, obj["display_field"])

            # Add properties for price and other parameters
            if obj.get("properties"):
                contains.property = []
                for prop_name in obj["properties"]:
                    if prop_name in item:
                        prop = {
                            "code": prop_name,
                            "valueString": str(item[prop_name])
                        }
                        contains.property.append(prop)

            expansion.contains.append(contains)

        expansion.total = len(expansion.contains)
        fhir_value_set.expansion = expansion
