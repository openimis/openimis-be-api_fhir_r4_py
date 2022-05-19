from rest_framework.authentication import SessionAuthentication
from core.jwt import *
from api_fhir_r4.views.login_viewset import LoginView


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return
