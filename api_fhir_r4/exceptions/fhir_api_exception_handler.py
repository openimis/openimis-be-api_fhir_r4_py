from rest_framework import status

from api_fhir_r4.configurations import ModuleConfiguration
from api_fhir_r4.utils import FunctionUtils
from rest_framework.response import Response

from rest_framework.views import exception_handler


def call_default_exception_handler(exc, context):
    response = None
    handler = ModuleConfiguration.get_default_api_error_handler()
    if handler:
        # Call default exception handler which can be defined in separate IMIS handler
        func = FunctionUtils.get_function_by_str(handler)
        if func:
            response = func(exc, context)
    else:
        # Call REST framework's default exception handler first, to get the standard error response.
        response = exception_handler(exc, context)
    return response


def fhir_api_exception_handler(exc, context):
    response = call_default_exception_handler(exc, context)

    request_path = __get_path_from_context(context)
    if 'api_fhir_r4' in request_path:
        from api_fhir_r4.converters import OperationOutcomeConverter
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
