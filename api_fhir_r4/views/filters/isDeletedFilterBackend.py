from rest_framework.filters import BaseFilterBackend


class IsDeletedFilterBackend(BaseFilterBackend):
    """
    Hide soft-deleted rows from every FHIR view whose model has an `is_deleted`
    field, unless the request asks for them with `isDeleted=true` (OP-3254).

    Models without the field (the legacy validity_to ones) are left untouched:
    their views already filter on validity.
    """

    PARAMETER = "isDeleted"
    TRUE_VALUES = ("true", "1", "yes")

    def filter_queryset(self, request, queryset, view):
        model = getattr(queryset, "model", None)
        if model is None or not self._has_is_deleted(model):
            return queryset
        requested = request.query_params.get(self.PARAMETER, "false")
        return queryset.filter(is_deleted=requested.strip().lower() in self.TRUE_VALUES)

    @staticmethod
    def _has_is_deleted(model):
        return any(field.name == "is_deleted" for field in model._meta.get_fields())
