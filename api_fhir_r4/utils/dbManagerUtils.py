from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
from django.shortcuts import get_object_or_404, get_list_or_404


class DbManagerUtils(object):

    __FIRST = 0

    @classmethod
    def get_object_or_none(cls, model, **kwargs):
        try:
            result = get_object_or_404(model, **kwargs)
        except MultipleObjectsReturned:
            result = get_list_or_404(model, validity_to__isnull=True, **kwargs)[cls.__FIRST]
        except Http404:
            result = None
        return result
