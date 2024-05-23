from drf_spectacular.utils import extend_schema, extend_schema_view
from graphql_jwt.utils import jwt_payload

from api_fhir_r4.openapi_schema_extensions import get_inline_login_request_serializer, \
    get_inline_login_200_response_serializer
from core.jwt import *
from core.models import User
from core.services import user_authentication
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import exceptions


@extend_schema_view(
    create=extend_schema(
        request=get_inline_login_request_serializer(),
        responses={
            (200, 'application/json'): get_inline_login_200_response_serializer(),
            (400,): None,
            (401,): None
        }
    )
)
class LoginView(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        data = request.data
        # check if we have both required data in request payload

        username = data.get('username')
        password = data.get('password')
        try:
            request.user = user_authentication(request, username, password)
        except exceptions.ParseError as e:
            return Response(str(e), status=400)
        except exceptions.AuthenticationFailed as e:
            return Response(str(e), status=401)
        if request.user:
            # take the payload base on user data - using same mechanism as
            # in graphql_jwt with generating payload.
            payload = jwt_payload(user=request.user)
            # encode token based on payload
            token = jwt_encode_user_key(payload=payload, context=request)
            if token:
                # return ok
                response = {
                    "token": token,
                    "exp": payload['exp'],
                }
                return Response(data=response, status=200)
            # return unauthorized
            return Response(status=401)
        else:
            # return bad request
            return Response(status=400)
