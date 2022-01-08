from abc import ABC, abstractmethod
from datetime import timedelta

from django.db.models import QuerySet
from typing import Dict, Callable, Any

from core.datetimes.ad_datetime import datetime


class QuerysetFilterABC(ABC):
    def __init__(self, field, value):
        self.field = field
        self.value = value

    @abstractmethod
    def apply_filter(self, queryset: QuerySet) -> QuerySet:
        """
        apply_filter should apply contained filter to given queryset and return the result.
        @param queryset: queryset the filter should be applied to
        @return: filtered queryset
        """
        pass


class QuerysetEqualFilter(QuerysetFilterABC):
    def apply_filter(self, queryset):
        return queryset.filter(**{self.field: self.value})


class QuerysetNotEqualFilter(QuerysetFilterABC):
    def apply_filter(self, queryset):
        return queryset.exclude(**{self.field: self.value})


class QuerysetGreaterThanFilter(QuerysetFilterABC):
    def apply_filter(self, queryset):
        return queryset.filter(**{f'{self.field}__gt': self.value})


class QuerysetLesserThanFilter(QuerysetFilterABC):
    def apply_filter(self, queryset):
        return queryset.filter(**{f'{self.field}__lt': self.value})


class QuerysetGreaterThanEqualFilter(QuerysetFilterABC):
    def apply_filter(self, queryset):
        return queryset.filter(**{f'{self.field}__gte': self.value})


class QuerysetLesserThanEqualFilter(QuerysetFilterABC):
    def apply_filter(self, queryset):
        return queryset.filter(**{f'{self.field}__lte': self.value})


class QuerysetApproximateDateFilter(QuerysetFilterABC):
    def apply_filter(self, queryset):
        range_size = (datetime.now() - self.value).days * 0.1
        value_start = self.value - timedelta(days=range_size)
        value_end = self.value + timedelta(days=range_size)
        return queryset.filter(**{f'{self.field}__range': (value_start, value_end)})


class QuerysetParameterABC(ABC):
    def __init__(self, output_parameter):
        self.output_parameter = output_parameter
        self.accepted_prefixes = self._get_prefix_filter_mapping().keys()

    @abstractmethod
    def _get_prefix_filter_mapping(self) -> Dict[str, Callable[[str, Any], QuerysetFilterABC]]:
        """
        _get_prefix_filter_mapping should return a dict that maps respective prefixes from FHIR specification to lambdas
        capable of creating specific filters taking affected field and parsed parameter value as arguments.
        @return: {prefix: lambda creating filter} map
        """
        pass

    def build_filter(self, request_parameter_value):
        modifier, value = self._get_prefix_and_value(request_parameter_value)
        return self._get_prefix_filter_mapping()[modifier if modifier else 'eq'](self.output_parameter, value)

    def _get_prefix_and_value(self, parameter):
        modifier = next((modifier for modifier in self.accepted_prefixes if parameter.startswith(modifier)), '')
        output_value = self._parse_value(parameter[len(modifier):])
        return modifier, output_value

    def _parse_value(self, value):
        """
        Allow for custom parameter value parsing logic. _parse_value in case of parsing error should raise Value error
        with message containing {request_parameter} placeholder to insert parameter name
        @param value: value to be parsed
        @return: parsed value
        """
        return value


class QuerysetLastUpdatedParameter(QuerysetParameterABC):
    def _get_prefix_filter_mapping(self):
        return {
            'eq': lambda field, value: QuerysetEqualFilter(field, value),
            'ne': lambda field, value: QuerysetNotEqualFilter(field, value),
            'gt': lambda field, value: QuerysetGreaterThanFilter(field, value),
            'lt': lambda field, value: QuerysetLesserThanFilter(field, value),
            'ge': lambda field, value: QuerysetGreaterThanEqualFilter(field, value),
            'le': lambda field, value: QuerysetLesserThanEqualFilter(field, value),
            'sa': lambda field, value: QuerysetGreaterThanEqualFilter(field, value),
            'eb': lambda field, value: QuerysetLesserThanEqualFilter(field, value),
            'ap': lambda field, value: QuerysetApproximateDateFilter(field, value)
        }

    def _parse_value(self, value):
        try:
            return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
        except Exception:
            raise ValueError('{request_parameter} value is not a valid datetime')


class RequestParameterFilterABC(ABC):
    def __init__(self, request):
        self.request = request

    @abstractmethod
    def _get_parameter_mapping(self) -> Dict[str, Callable[[], QuerysetParameterABC]]:
        """
        _get_parameter_mapping should return a dict mapping request parameters to lambdas capable of creating
        filters (allowing lazy loading)
        @return: {request parameter: lambda creating queryset parameter} map
        """
        pass

    def filter_queryset(self, queryset):
        parameter_mapping = self._get_parameter_mapping()
        accepted_parameters = parameter_mapping.keys()
        request_parameters = {parameter: self.request.GET[parameter]
                              for parameter in accepted_parameters if parameter in self.request.GET}

        output_queryset = queryset
        for request_parameter in request_parameters:
            output_parameter = parameter_mapping[request_parameter]()
            try:
                output_queryset = output_parameter.build_filter(self.request.GET[request_parameter]).apply_filter(
                    output_queryset)
            except ValueError as parsingError:
                raise ValueError(str(parsingError).format(**{'request_parameter': request_parameter}))

        return output_queryset


class ValidityFromRequestParameterFilter(RequestParameterFilterABC):
    def _get_parameter_mapping(self):
        return {
            '_lastUpdated': lambda: QuerysetLastUpdatedParameter('validity_from'),
        }


class DateUpdatedRequestParameterFilter(RequestParameterFilterABC):
    def _get_parameter_mapping(self):
        return {
            '_lastUpdated': lambda: QuerysetLastUpdatedParameter('date_updated'),
        }
