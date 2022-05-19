from drf_spectacular.utils import extend_schema, extend_schema_view
from graphql_jwt.utils import jwt_payload

from api_fhir_r4.openapi_schema_extensions import get_inline_login_request_serializer, \
    get_inline_login_200_response_serializer
from core.jwt import *
from core.models import User
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema_view(
    create=extend_schema(
        request=get_inline_login_request_serializer(),
        responses={
            (200, 'application/json'): get_inline_login_200_response_serializer(),
            (401,): None
        }
    )
)
class LoginView(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        data = request.data
        # check if we have both required data in request payload
        if 'username' in data and 'password' in data:
            username = data['username']
            password = data['password']
            users = User.objects.filter(username=username)
            # check if user with such username exists
            if len(list(users)) == 1:
                # validate provided password from payload
                user = users.first()
                if user.check_password(password):
                    # set the user to context
                    request.user = user
                    # take the payload base on user data - using same mechanism as
                    # in graphql_jwt with generating payload.
                    payload = jwt_payload(user=user)
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
