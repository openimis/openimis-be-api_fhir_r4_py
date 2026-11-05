from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext


class FHIRException(APIException):
    """Base for FHIR request problems.

    Every exception in this module describes something wrong with the *request*
    -- a missing mandatory element, an attribute that is not part of the
    resource, a value that is too long. They used to inherit
    ``APIException.status_code``, which is 500, so a FHIR client could not tell
    "your resource is invalid" from "the server is broken" and retry logic would
    keep retrying a request that can never succeed. 4xx is the correct class.
    """

    status_code = status.HTTP_400_BAD_REQUEST

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


class PropertyTypeError(FHIRException):
    def __init__(self, local_type, description):
        msg = gettext("Expected '{}' but got '{}' for '{}' property").format(
            description.type, local_type, description.name
        )
        super(PropertyTypeError, self).__init__(msg)


class UnsupportedFormatError(FHIRException):
    # A format the server cannot consume is a media-type problem, not a bad value.
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    def __init__(self, data_format):
        message = gettext("The format '{}' is not supported").format(data_format)
        super(UnsupportedFormatError, self).__init__(message)
