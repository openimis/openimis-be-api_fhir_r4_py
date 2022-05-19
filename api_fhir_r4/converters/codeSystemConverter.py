from api_fhir_r4.converters import BaseFHIRConverter
from fhir.resources.codesystem import CodeSystem, CodeSystemConcept

from api_fhir_r4.utils import FhirUtils


class CodeSystemConverter(BaseFHIRConverter):

    @classmethod
    def to_imis_obj(cls, data, audit_user_id):
        raise NotImplementedError('`toImisObj()` not implemented.')  # pragma: no cover

    @classmethod
    def get_fhir_code_identifier_type(cls):
        raise NotImplementedError('`get_fhir_code_identifier_type()` not implemented.')  # pragma: no cover

    @classmethod
    def to_fhir_obj(cls, obj, reference_type):
        fhir_code_system = {}
        cls.build_fhir_code_system_status(fhir_code_system)
        cls.build_fhir_code_system_content(fhir_code_system)
        fhir_code_system = CodeSystem(**fhir_code_system)
        cls.build_fhir_id(fhir_code_system, obj)
        cls.build_fhir_url(fhir_code_system, obj)
        cls.build_fhir_code_system_name(fhir_code_system, obj)
        cls.build_fhir_code_system_title(fhir_code_system, obj)
        cls.build_fhir_code_system_date(fhir_code_system)
        cls.build_fhir_code_system_description(fhir_code_system, obj)
        cls.build_fhir_code_system_count(fhir_code_system, obj)
        cls.build_fhir_code_system_concept(fhir_code_system, obj)
        return fhir_code_system

    @classmethod
    def build_fhir_id(cls, fhir_code_system, obj):
        fhir_code_system.id = obj['id']

    @classmethod
    def build_fhir_url(cls, fhir_code_system, obj):
        fhir_code_system.url = obj['url']

    @classmethod
    def build_fhir_code_system_name(cls, fhir_code_system, obj):
        fhir_code_system.name = obj['name']

    @classmethod
    def build_fhir_code_system_title(cls, fhir_code_system, obj):
        fhir_code_system.title = obj['title']

    @classmethod
    def build_fhir_code_system_date(cls, fhir_code_system):
        from core.utils import TimeUtils
        fhir_code_system.date = TimeUtils.now()

    @classmethod
    def build_fhir_code_system_description(cls, fhir_code_system, obj):
        fhir_code_system.description = obj['description']

    @classmethod
    def build_fhir_code_system_status(cls, fhir_code_system):
        fhir_code_system['status'] = 'active'

    @classmethod
    def build_fhir_code_system_content(cls, fhir_code_system):
        fhir_code_system['content'] = 'complete'

    @classmethod
    def build_fhir_code_system_count(cls, fhir_code_system, obj):
        fhir_code_system.count = f'{len(obj["data"])}'

    @classmethod
    def build_fhir_code_system_concept(cls, fhir_code_system, obj):
        fhir_code_system.concept = []
        for item in obj["data"]:
            code_system_concept = CodeSystemConcept.construct()
            code_system_concept.code = FhirUtils.get_attr(item, obj["code_field"])
            code_system_concept.display = FhirUtils.get_attr(item, obj["display_field"])
            fhir_code_system.concept.append(code_system_concept)
