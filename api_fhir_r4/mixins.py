import logging
from abc import abstractmethod, ABC
from collections.abc import Iterable

from typing import List
from rest_framework import status

from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.http import Http404

from api_fhir_r4.model_retrievers import GenericModelRetriever
from rest_framework.response import Response
from core.models import HistoryModel
from api_fhir_r4.multiserializer.mixins import MultiSerializerUpdateModelMixin, MultiSerializerRetrieveModelMixin
from rest_framework.mixins import (
    CreateModelMixin as RestCreateModelMixin,
    UpdateModelMixin as RestUpdateModelMixin,
    ListModelMixin as RestListModelMixin,
    DestroyModelMixin as RestDestroyModelMixin,
    RetrieveModelMixin as RestRetrieveModelMixin,
)

logger = logging.getLogger(__name__)


class CreateModelMixin(RestCreateModelMixin):

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, user=request.user)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class UpdateModelMixin(RestUpdateModelMixin):
    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, user=request.user)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
    
    
class ListModelMixin(RestListModelMixin):
    """
    List a queryset.
    """
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if not isinstance(queryset, Iterable):
            queryset = queryset.all().order_by('code' if hasattr(queryset.model, 'code') else 'id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, user=request.user)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class DestroyModelMixin(RestDestroyModelMixin):
    """
    Destroy a model instance.
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.user = request.user
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        if issubclass(instance.__class__, HistoryModel):
            instance.delete(user=self.user)
        else:
            instance.delete()
            
            
class RetrieveModelMixin(RestRetrieveModelMixin):
    """
    Retrieve a model instance.
    """
    def retrieve(self, request, *args, **kwargs):
        self.user = request.user
        instance = self.get_object()
        serializer = self.get_serializer(instance, user=self.user)
        return Response(serializer.data)


class GenericMultiIdentifierMixin(ABC):
    lookup_field = 'identifier'

    @property
    @abstractmethod
    def retrievers(self) -> List[GenericModelRetriever]:
        # Identifiers available for given resource
        pass

    def _get_object_with_first_valid_retriever(self, identifier):
        for retriever in self.retrievers:
            if retriever.identifier_validator(identifier):
                try:
                    queryset = retriever.retriever_additional_queryset_filtering(self.get_queryset())
                    resource = retriever.get_model_object(queryset, identifier)

                    # May raise a permission denied
                    self.check_object_permissions(self.request, resource)
                    return retriever.serializer_reference_type, resource
                except ObjectDoesNotExist as e:
                    logger.exception(
                        F"Failed to retrieve object from queryset {self.get_queryset()} using"
                        F"identifier {identifier} for matching retriever: {retriever}"
                    )

        # Raise Http404 if resource couldn't be fetched with any of the retrievers
        raise Http404(f"Resource for identifier {identifier} not found")


class MultiIdentifierRetrieverMixin(RetrieveModelMixin, GenericMultiIdentifierMixin, ABC):

    def retrieve(self, request, *args, **kwargs):
        ref_type, instance = self._get_object_with_first_valid_retriever(kwargs['identifier'])
        serializer = self.get_serializer(instance, reference_type=ref_type, user=request.user)
        return Response(serializer.data)


class MultiIdentifierUpdateMixin(UpdateModelMixin, GenericMultiIdentifierMixin, ABC):

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        ref_type, instance = self._get_object_with_first_valid_retriever(kwargs['identifier'])
        serializer = self.get_serializer(instance, data=request.data, partial=partial, reference_type=ref_type, user=request.user)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class GenericMultiIdentifierForManySerializers(GenericMultiIdentifierMixin, ABC):

    def _get_object_with_first_valid_retriever(self, queryset, identifier):
        for retriever in self.retrievers:
            if retriever.identifier_validator(identifier):
                try:
                    queryset = retriever.retriever_additional_queryset_filtering(queryset)
                    resource = retriever.get_model_object(queryset, identifier)

                    # May raise a permission denied
                    self.check_object_permissions(self.request, resource)
                    return retriever.serializer_reference_type, resource
                except ObjectDoesNotExist:
                    logger.exception(
                        F"Failed to retrieve object from queryset {queryset} using"
                        F"identifier {identifier} for matching retriever: {retriever}"
                    )
                except FieldError:
                    logger.exception(F"Failed to retrieve object from queryset {queryset} using"
                                     F"{self.lookup_field}, field does not available for given model {queryset.model}")
        return None, None


class MultiIdentifierUpdateManySerializersMixin(MultiSerializerUpdateModelMixin,
                                                GenericMultiIdentifierForManySerializers, ABC):
    def update(self, request, *args, **kwargs):
        self._validate_update_request()
        partial = kwargs.pop('partial', False)
        results = []
        for serializer, (qs, _, _) in self.get_eligible_serializers_iterator():
            ref_type, instance = self._get_object_with_first_valid_retriever(qs, kwargs['identifier'])
            update_result = self._update_for_serializer(serializer, instance, request.data, partial,
                                                        reference_type=ref_type, user=request.user)
            results.append(update_result)

        response = results[0]  # By default there should be only one eligible serializer
        return Response(response)


class MultiIdentifierRetrieveManySerializersMixin(MultiSerializerRetrieveModelMixin,
                                                  GenericMultiIdentifierForManySerializers, ABC):
    def retrieve(self, request, *args, **kwargs):
        self._validate_retrieve_model_request()
        retrieved = []
        for serializer, (qs, _, _) in self.get_eligible_serializers_iterator():
            ref_type, instance = self._get_object_with_first_valid_retriever(qs, kwargs['identifier'])
            if instance:
                serializer = serializer(instance, reference_type=ref_type, user=request.user)
                if serializer.data:
                    retrieved.append(serializer.data)

        if len(retrieved) > 1:
            raise ValueError("Ambiguous retrieve result, object found for multiple serializers.")
        if len(retrieved) == 0:
            raise Http404(f"Resource for identifier {kwargs['identifier']} not found")

        return Response(retrieved[0])

