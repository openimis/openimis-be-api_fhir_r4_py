from rest_framework import status
from rest_framework.response import Response
from rest_framework import exceptions, status, views
from api_fhir_r4.exceptions import FHIRException

from django.conf import settings
import traceback
import logging

logger = logging.getLogger(__name__)

def call_default_exception_handler(exc, context):
    # Call REST framework's default exception handler first, to get the standard error response.
    response = views.exception_handler(exc, context)

    if isinstance(exc, (exceptions.AuthenticationFailed, exceptions.NotAuthenticated)):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response
    return response


def fhir_api_exception_handler(exc, context):
    response = call_default_exception_handler(exc, context)

    request_path = __get_path_from_context(context)
    if 'api_fhir_r4' in request_path:
        from api_fhir_r4.converters import OperationOutcomeConverter
        fhir_outcome = OperationOutcomeConverter.to_fhir_obj(exc)
        if settings.DEBUG and not isinstance(exc, (
            exceptions.NotAuthenticated,
            exceptions.AuthenticationFailed,
            exceptions.PermissionDenied,
            FHIRException
        )):
            trace = traceback.extract_tb(traceback.sys.exc_info()[2])
            logger.debug("Unexpected {exc.__class__.__name__} trace:\n" + ''.join(traceback.format_list(trace))) 

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
