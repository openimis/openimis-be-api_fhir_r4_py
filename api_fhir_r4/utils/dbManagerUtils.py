from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
from django.shortcuts import get_object_or_404, get_list_or_404


class DbManagerUtils(object):

    __FIRST = 0

    @classmethod
    def get_object_or_none(cls, model, **kwargs):
        if 'uuid' not in kwargs and id not in kwargs:
            if hasattr(cls, 'validity_to'):
                kwargs['validity_to__isnull'] = True
        try:
            result = get_object_or_404(model, **kwargs)
        except MultipleObjectsReturned:
            result = get_list_or_404(model, **kwargs)[cls.__FIRST]
        except Http404:
            result = None
        return result
