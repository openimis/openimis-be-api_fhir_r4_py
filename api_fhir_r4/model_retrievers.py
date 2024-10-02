import uuid
from abc import ABC, abstractmethod, abstractproperty
from typing import Union

from django.db.models.query import QuerySet
from django.db.models import Model
from insuree.services import validate_insuree_number
from api_fhir_r4.converters import ReferenceConverterMixin
from django.core.exceptions import ValidationError

class GenericModelRetriever(ABC):

    @property
    @abstractmethod
    def identifier_field(self) -> str:
        pass

    @property
    @abstractmethod
    def serializer_reference_type(self) -> Union[
        ReferenceConverterMixin.UUID_REFERENCE_TYPE,
        ReferenceConverterMixin.CODE_REFERENCE_TYPE,
        ReferenceConverterMixin.DB_ID_REFERENCE_TYPE
    ]:
        pass

    @classmethod
    @abstractmethod
    def identifier_validator(cls, identifier_value) -> bool:
        pass

    @classmethod
    def retriever_additional_queryset_filtering(cls, queryset):
        # By default no additional changes are made in queryset
        return queryset

    @classmethod
    def get_model_object(cls, queryset: QuerySet, identifier_value) -> Model:
        filters = {}
        if cls.serializer_reference_type == 'uuid_reference':
            identifier_value = uuid.UUID(str(identifier_value))
        elif hasattr(queryset.model, 'validity_to'):  
            filters['validity_to__isnull'] = True
        filters[cls.identifier_field] = identifier_value
        try:
            return queryset.get(**filters)
        except Exception as e:
            raise ValidationError(f"failed to retrieve {queryset.model.__name__} with the filter {filters}; details {e}")


class UUIDIdentifierModelRetriever(GenericModelRetriever):
    identifier_field = 'uuid'
    serializer_reference_type = ReferenceConverterMixin.UUID_REFERENCE_TYPE

    @classmethod
    def identifier_validator(cls, identifier_value):
        return cls._is_uuid_identifier(identifier_value)

    @classmethod
    def _is_uuid_identifier(cls, identifier):
        try:
            uuid.UUID(str(identifier))
            return True
        except ValueError:
            return False


class DatabaseIdentifierModelRetriever(GenericModelRetriever):
    identifier_field = 'id'
    serializer_reference_type = ReferenceConverterMixin.DB_ID_REFERENCE_TYPE

    @classmethod
    def identifier_validator(cls, identifier_value):
        return isinstance(identifier_value, int) or identifier_value.isdigit()


class CodeIdentifierModelRetriever(GenericModelRetriever):
    identifier_field = 'code'
    serializer_reference_type = ReferenceConverterMixin.CODE_REFERENCE_TYPE

    @classmethod
    def identifier_validator(cls, identifier_value):
        return isinstance(identifier_value, str)

    


class CHFIdentifierModelRetriever(CodeIdentifierModelRetriever):
    identifier_field = 'chf_id'

    @classmethod
    def identifier_validator(cls, identifier_value):
        # From model specification
        return isinstance(identifier_value, str) and validate_insuree_number(identifier_value)


class GroupIdentifierModelRetriever(CHFIdentifierModelRetriever):
    identifier_field = 'head_insuree_id__chf_id'

