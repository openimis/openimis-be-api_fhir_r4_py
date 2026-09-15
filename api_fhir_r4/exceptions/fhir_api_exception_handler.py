from rest_framework.response import Response
from rest_framework import exceptions, status, views
from api_fhir_r4.exceptions import FHIRException

import logging

try:
    from sentry_sdk import capture_exception
    from sentry_sdk.integrations.logging import ignore_logger
except ImportError:  # sentry_sdk is optional (see sentry-requirements.txt)
    def capture_exception(_exception):
        """No-op when sentry_sdk is not installed."""
        return None

    def ignore_logger(_name):
        return None

logger = logging.getLogger(__name__)

# Unexpected failures are reported explicitly below; let Sentry's logging
# integration skip this logger rather than raise a second event for the same
# exception.
ignore_logger(__name__)


def call_default_exception_handler(exc, context):
    # Call REST framework's default exception handler first, to get the standard error response.
    response = views.exception_handler(exc, context)

    if isinstance(exc, (exceptions.AuthenticationFailed, exceptions.NotAuthenticated)):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response
    return response


# Exceptions that describe the caller's own request: their message is written
# for the client, and they are not server faults worth a traceback.
EXPECTED_EXCEPTIONS = (
    exceptions.NotAuthenticated,
    exceptions.AuthenticationFailed,
    exceptions.PermissionDenied,
    FHIRException,
)


def fhir_api_exception_handler(exc, context):
    response = call_default_exception_handler(exc, context)

    request_path = __get_path_from_context(context)
    if "api_fhir_r4" in request_path:
        from api_fhir_r4.converters import OperationOutcomeConverter

        unexpected = not isinstance(exc, EXPECTED_EXCEPTIONS)
        if unexpected:
            # Was previously guarded by settings.DEBUG, which is False in
            # production -- so the one environment where an unexpected FHIR
            # failure matters was the one that recorded nothing about it.
            # exc_info=exc rather than sys.exc_info(): correct even when this
            # runs outside the original except block.
            logger.error(
                "Unexpected %s handling %s",
                exc.__class__.__name__,
                request_path,
                exc_info=exc,
            )
            # DRF turns this into a response, so it is a *handled* exception and
            # Sentry's Django integration never sees it.
            capture_exception(exc)

        fhir_outcome = OperationOutcomeConverter.to_fhir_obj(exc)

        if not response:
            response = __create_server_error_response()

        response.data = fhir_outcome.dict()

    return response


def __get_path_from_context(context):
    result = ""
    request = context.get("request")
    if request and request._request:
        result = request._request.path
    return result


def __create_server_error_response():
    return Response(None, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
