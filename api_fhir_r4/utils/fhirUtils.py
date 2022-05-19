class FhirUtils(object):
    __ARRAY_ID_OFFSET = 1  # used to start iterating from 1

    @classmethod
    def get_next_array_sequential_id(cls, array):
        if array is None:
            array = []
        return len(array) + cls.__ARRAY_ID_OFFSET

    @classmethod
    def get_attr(cls, obj, field):
        if isinstance(obj, dict):
            return obj[field]
        else:
            return getattr(obj, field)
