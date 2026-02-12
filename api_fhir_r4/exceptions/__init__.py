from rest_framework.exceptions import APIException
from django.utils.translation import gettext


class FHIRException(APIException):
    def __init__(self, message):
        super(FHIRException, self).__init__(message)


class FHIRRequestProcessException(FHIRException):
    def __init__(self, errors):
        base_massage = gettext(
            "The request cannot be processed due to the following issues:\n"
        )
        message = base_massage + ",\n".join(errors)
        super(FHIRRequestProcessException, self).__init__(message)


class InvalidAttributeError(FHIRException):
    def __init__(self, attr, property_type):
        msg = gettext(
            "The attribute named '{}' is not a valid property for '{}'."
        ).format(attr, property_type)
        super(InvalidAttributeError, self).__init__(msg)


class PropertyError(FHIRException):
    def __init__(self, message):
        super(PropertyError, self).__init__(message)


class PropertyMaxSizeError(PropertyError):
    def __init__(self, definition):
        message = gettext("The max size was exceeded for property {} [{}..{}]").format(
            definition.name, definition.count_min, definition.count_max
        )
        super(PropertyMaxSizeError, self).__init__(message)


class PropertyTypeError(Exception):
    def __init__(self, local_type, description):
        msg = gettext("Expected '{}' but got '{}' for '{}' property").format(
            description.type, local_type, description.name
        )
        super(PropertyTypeError, self).__init__(msg)


class UnsupportedFormatError(Exception):
    def __init__(self, data_format):
        message = gettext("The format '{}' is not supported").format(data_format)
        super(UnsupportedFormatError, self).__init__(message)
