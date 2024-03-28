"""
Basic building blocks for generic class based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from itertools import chain
from typing import Dict, Type, Callable, Iterable, Tuple, List

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.serializers import Serializer
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.http import Http404
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist, FieldError

from api_fhir_r4.permissions import FHIRApiPermissions

logger = logging.getLogger(__name__)


def _MultiserializerPermissionClassWrapper(PermissionClass):
    def has_permission(self, request, view, queryset):
        if getattr(view, '_ignore_model_permissions', False):
            return True

        if not request.user or (not request.user.is_authenticated and self.authenticated_users_only):
            return False
        
        #read access can be defined by the ability to get a queryset
        if request.method == 'GET' and self.base_class:
            qs =  self.base_class.get_queryset()
            if qs is None:
                return False
            filter_values = qs.filter_values()
            # filter(id=-1) is used to return an empty qs
            if filter_values.get('id') == -1:
                return False
        perms = self.get_required_permissions(request.method, queryset.model)
        return request.user.has_perms(perms)

    permission_class = type('PermissionClassWrapper', PermissionClass.__bases__, dict(PermissionClass.__dict__))
    permission_class.has_permission = has_permission
    return permission_class


class GenericMultiSerializerViewsetMixin(ABC):

    @property
    def permission_classes(self):
        """
        Multi-serializer classes should use permissions added to registered serializers, instead for viewset directly.
        Initial permission check is used only to validate if request is validated with user.
        Returns:

        """
        return (IsAuthenticated,)

    def get_serializer_class(self):
        """
        serializer_class is not meant to be used in Multiserializer viewset context
        """
        pass

    @property
    def serializer_class(self):
        raise NotImplementedError("serializer_class is not meant to be used in Multiserializer viewset context")

    @property
    @abstractmethod
    def serializers(self) \
            -> Dict[Type[Serializer], Tuple[Callable[[], QuerySet], Callable[[Dict], bool], Tuple[FHIRApiPermissions]]]:
        """
        Variable used for determining serializers available for the given viewset. It's a dictionary where keys
        are serializers and values are tuples with two functions.
        First one is responsible for returning queryset used by the serializer.
        Second one is validator function responsible for determining if given serializer
        is eligible for request context.
        Third element is tuple of permissions, as ViewSet doesn't provide permission check for endpoint it's required
        to validate permissions against specific serializers. If user doesn't have permission for any serializer then
        401 is raised.
        Returns:

        """
        raise NotImplementedError('serializers method has to return dictionary of serializers')

    def get_eligible_serializers(self) -> List[Type[Serializer]]:
        eligible = []
        context = self.get_serializer_context()

        eligible_from_permissions = self._get_eligible_from_user_permissions()

        for serializer, (queryset, eligibility_validator, permission_class) in self.serializers.items():
            if eligibility_validator(context) and serializer in eligible_from_permissions:
                eligible.append(serializer)
        return eligible

    def _aggregate_results(self, results):
        """
        It's expected for serializers to aggregate output data in format that will be accepted by
        rest_framework.Response as data argument.
        By default it returns first argument
        :param results: Results for execution of actions on individual serializers
        :return: By default returns result in raw format.
        """
        return results

    def get_object_by_queryset(self, qs):
        """
        Adjusted Django Rest Framework's GenericAPIView
        """

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        queryset = self.filter_queryset(qs)

        try:
            filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
            obj = queryset.get(**filter_kwargs)
            # May raise a permission denied
            self.check_object_permissions(self.request, obj)
        except (ObjectDoesNotExist, PermissionDenied):
            return None
        except FieldError as e:
            logger.warning(F"Fetching object with multiserializer has failed, lookup field {self.lookup_field} does"
                           F"not exist for {queryset.model}: {str(e)}")
            return None
        return obj

    def validate_single_eligible_serializer(self):
        eligible_serializers = len(self.get_eligible_serializers())
        if eligible_serializers == 0:
            self._raise_no_eligible_serializer()
        if eligible_serializers > 1:
            self._raise_multiple_eligible_serializers()

    def get_eligible_serializers_iterator(self):
        for serializer in self.get_eligible_serializers():
            yield serializer, self.serializers[serializer]

    def _raise_no_eligible_serializer(self):
        raise AssertionError("Failed to match serializer eligible for given request")

    def _raise_multiple_eligible_serializers(self):
        raise AssertionError("Ambiguous request, more than one serializer is eligible for given action")

    def _get_eligible_from_user_permissions(self):
        eligible_serializers = []
        for serializer, (queryset, eligibility_validator, permission_classes) in self.serializers.items():
            permission_classes = [
                _MultiserializerPermissionClassWrapper(perm_cls)() for perm_cls in permission_classes
            ]
            if all([p.has_permission(self.request, self, queryset) for p in permission_classes]):
                eligible_serializers.append(serializer)

        if len(eligible_serializers) == 0:
            self.permission_denied(
                self.request,
                message="User unauthorized for any of the resourceType available in the view."
            )

        return eligible_serializers


class MultiSerializerCreateModelMixin(GenericMultiSerializerViewsetMixin, ABC):
    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        self._validate_create_request()
        results = []
        for serializer, _ in self.get_eligible_serializers_iterator():
            data = self._create_for_serializer(serializer, request, *args, **kwargs)
            results.append(data)

        headers = self.get_success_headers(results)
        response = results[0]  # By default there should be only one eligible serializer
        return Response(response, status=status.HTTP_201_CREATED, headers=headers)

    def _create_for_serializer(self, serializer, request, *args, **kwargs):
        context = self.get_serializer_context()  # Required for audit user id
        serializer = serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return serializer.data

    def perform_create(self, serializer):
        serializer.save()

    def get_success_headers(self, res):
        try:
            return {'Location': str([data[api_settings.URL_FIELD_NAME] for data in res])}
        except (TypeError, KeyError):
            return {}

    def _validate_create_request(self):
        self.validate_single_eligible_serializer()


class _JoinedQuerysets:
    def __init__(self, *qs):
        self.querysets = qs

    def __iter__(self):
        return chain(self.querysets)

    def __len__(self):
        return sum([len(qs) for qs in self.querysets])

    def __getitem__(self, k):
        if not isinstance(k, (int, slice)):
            raise TypeError

        return self.__get_queryset_for_item(k)

    def __get_queryset_for_item(self, k):
        if isinstance(k, int):
            return self.__get_queryset_for_index(k)
        else:
            # slice
            if k.step:
                raise ValidationError("Step not supported in joined queryset context.")
            start, end = int(k.start) if k else None, int(k.stop) if k else None
            intersection = [None, None]
            final_query = []
            if start:
                start_qs, qs_idx = self.__get_queryset_for_index(start)
                intersection[0] = self.querysets.index(start_qs) + 1
                start_qs = start_qs.all()[qs_idx:]
            if end:
                end_qs, qs_idx = self.__get_queryset_for_index(end)
                intersection[1] = self.querysets.index(end_qs)
                end_qs = end_qs.all()[:qs_idx]

            if start:
                final_query.append(start_qs)

            final_query.extend(self.querysets[intersection[0]:intersection[1]])

            if end:
                final_query.append(end_qs)

            return list(chain(*final_query))

    def __get_queryset_for_index(self, k):
        """
        Return queryset for which given index is relevant. If given index is out of range it raises IndexEr
        Args:
            k: index of element.

        Returns:
            Tuple of queryset and index k relative for given queryset

        """
        next_queryset_last_index = 0
        for qs in self.querysets:
            qs_len = qs.count()
            next_queryset_last_index += qs_len
            if k < next_queryset_last_index:
                index_in_queryset = k - (next_queryset_last_index - qs_len)
                return qs, index_in_queryset
            if k == next_queryset_last_index:
                return qs, 0
        raise IndexError(f"for index {k}")

    def count(self):
        return sum([qs.count() for qs in self.querysets])


class MultiSerializerListModelMixin(GenericMultiSerializerViewsetMixin, ABC):
    """
    List a queryset.
    """
    def list(self, request, *args, **kwargs):
        self._validate_list_model_request()
        filtered_querysets = {}  # {serialzer: qs}

        for serializer, (qs, _, _) in self.get_eligible_serializers_iterator():
            next_serializer_data = self.filter_queryset(qs)
            model = next_serializer_data.model
            filtered_querysets[model, serializer] = next_serializer_data

        if not filtered_querysets:
            return {}

        try:
            querysets = self._join_querysets([*filtered_querysets.values()])
            page = self.paginate_queryset(querysets)
            data = self.__dispatch_page_data(page)
            serialized_data = self._serialize_dispatched_data(data, dict(filtered_querysets.keys()))
            data = self.get_paginated_response(serialized_data)
            return data
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    def _validate_list_model_request(self):
        # By default always valid
        return True

    def __dispatch_page_data(self, page):
        x = defaultdict(list)
        for r in page:
            x[type(r)].append(r)
        return x

    def _serialize_dispatched_data(self, data, serializer_models):
        serialized = []
        for model, model_data in data.items():
            serializer_cls = serializer_models.get(model, None)
            if not serializer_cls:
                logger.error(f"Found data of type {model_data} but it couldn't be matched with "
                             f"any of available serializers {serializer_models}")
                continue
            else:
                serializer = serializer_cls(tuple(model_data), many=True)
                serialized.extend(serializer.data)

        return serialized

    def _join_querysets(self, querysets: List[QuerySet]):
        if len(querysets) == 0:
            raise ValueError("At least one eligible queryset required.")
        elif len(querysets) == 1:
            return querysets[0]
        else:
            # Inefficient due to pulling every entry and not only paginated chunk
            chained = _JoinedQuerysets(*querysets)
            # Chain doesn't provide len, but it's required by paginator
            return chained


class MultiSerializerRetrieveModelMixin(GenericMultiSerializerViewsetMixin, ABC):
    """
    Retrieve a model instance.
    """
    def retrieve(self, request, *args, **kwargs):
        self._validate_retrieve_model_request()
        retrieved = []
        for serializer, (qs, _, _) in self.get_eligible_serializers_iterator():
            instance = self.get_object_by_queryset(qs=qs)
            serializer = serializer(instance)
            if serializer.data:
                retrieved.append(serializer.data)

        if len(retrieved) > 1:
            raise ValueError("Ambiguous retrieve result, object found for multiple serializers.")
        if len(retrieved) == 0:
            raise Http404

        return Response(retrieved[0])

    def _validate_retrieve_model_request(self):
        # By default always valid
        return True


class MultiSerializerUpdateModelMixin(GenericMultiSerializerViewsetMixin, ABC):
    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        self._validate_update_request()
        partial = kwargs.pop('partial', False)
        results = []
        for serializer, (qs, _, _) in self.get_eligible_serializers_iterator():
            instance = self.get_object_by_queryset(qs=qs)
            update_result = self._update_for_serializer(serializer, instance, request.data, partial)
            results.append(update_result)

        response = results[0]  # By default there should be only one eligible serializer
        return Response(response)

    def _update_for_serializer(self, serializer, instance, data, partial, *args, **kwargs):
        context = self.get_serializer_context()  # Required for audit user id
        serializer = serializer(instance, data=data, partial=partial, context=context, *args, **kwargs)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return serializer.data

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def _validate_update_request(self):
        self.validate_single_updatable_resource()

    def validate_single_updatable_resource(self):
        instance = None
        for serializer, (qs, _, _) in self.get_eligible_serializers_iterator():
            obj = self.get_object_by_queryset(qs=qs)
            if obj and instance:
                # If more than one updatable instance found
                return False
            elif obj:
                instance = obj
        return True
