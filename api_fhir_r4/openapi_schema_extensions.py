from drf_spectacular.authentication import SessionScheme, TokenScheme
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from drf_spectacular.utils import inline_serializer
from rest_framework import fields


class CsrfExemptAuthenticationScheme(SessionScheme):
    target_class = 'api_fhir_r4.views.CsrfExemptSessionAuthentication'
    name = "Session Authentication (CSRF Exempt)"
    priority = 0
    exclude = True


class JWTAuthenticationScheme(TokenScheme):
    target_class = 'core.jwt_authentication.JWTAuthentication'
    name = "JWT Authentication"
    priority = 0

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name='Authorization',
            token_prefix='Bearer',
        )


def get_inline_error_serializer():
    return inline_serializer(
        name='InlineErrorSerializer',
        fields={
            'resourceType': fields.CharField(),
            'issue': fields.ListField(child=fields.JSONField()),
        }
    )


def get_inline_login_request_serializer():
    return inline_serializer(
        name='InlineLoginRequestSerializer',
        fields={
            'username': fields.CharField(),
            'password': fields.CharField(),
        }
    )


def get_inline_login_200_response_serializer():
    return inline_serializer(
        name='InlineLoginResponseSerializer',
        fields={
            'token': fields.CharField(),
            'exp': fields.IntegerField(),
        }
    )
