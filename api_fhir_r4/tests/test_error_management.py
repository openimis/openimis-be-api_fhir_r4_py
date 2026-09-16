import logging
from types import SimpleNamespace

from django.test import TestCase
from rest_framework import exceptions, status

from api_fhir_r4.exceptions import (
    FHIRException,
    FHIRRequestProcessException,
    InvalidAttributeError,
    PropertyError,
    PropertyMaxSizeError,
    PropertyTypeError,
    UnsupportedFormatError,
)
from api_fhir_r4.exceptions.fhir_api_exception_handler import (
    fhir_api_exception_handler,
)


def fhir_context(path="/api/api_fhir_r4/Patient/"):
    """Minimal DRF-ish context: the handler only reads request._request.path."""
    return {"request": SimpleNamespace(_request=SimpleNamespace(path=path))}


class FHIRExceptionStatusTest(TestCase):
    """A malformed request must not be reported as a server fault.

    These all used to inherit APIException.status_code (500), so a FHIR client
    could not tell an invalid resource from a broken server, and retry logic
    would retry a request that can never succeed.
    """

    def test_request_problems_are_client_errors(self):
        cases = (
            FHIRException("bad resource"),
            FHIRRequestProcessException(["missing name"]),
            InvalidAttributeError("nope", "Patient"),
            PropertyError("bad property"),
            PropertyTypeError(
                "str", SimpleNamespace(type="int", name="age", count_min=0, count_max=1)
            ),
            PropertyMaxSizeError(
                SimpleNamespace(name="name", count_min=0, count_max=1)
            ),
        )
        for exc in cases:
            with self.subTest(type(exc).__name__):
                self.assertTrue(
                    status.is_client_error(exc.status_code),
                    f"{type(exc).__name__} reports {exc.status_code}",
                )

    def test_unsupported_format_is_an_unsupported_media_type(self):
        self.assertEqual(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            UnsupportedFormatError("xml").status_code,
        )

    def test_orphan_exceptions_are_handled_as_fhir_exceptions(self):
        # Both used to subclass bare Exception, so DRF's handler returned None
        # and the handler fell through to a blanket 500.
        for cls in (PropertyTypeError, UnsupportedFormatError):
            with self.subTest(cls.__name__):
                self.assertTrue(issubclass(cls, FHIRException))


class FHIRExceptionHandlerLoggingTest(TestCase):
    """Unexpected failures must be recorded, in production above all.

    The traceback used to be logged only when settings.DEBUG was true, so the
    one environment where an unexpected FHIR failure matters recorded nothing.
    Django's test runner forces DEBUG off, so these run production-like.
    """

    def test_unexpected_exception_is_logged_with_traceback(self):
        with self.assertLogs(
            "api_fhir_r4.exceptions.fhir_api_exception_handler", level=logging.ERROR
        ) as captured:
            fhir_api_exception_handler(RuntimeError("db exploded"), fhir_context())

        self.assertEqual(1, len(captured.records))
        record = captured.records[0]
        self.assertIsNotNone(record.exc_info, "traceback was not attached")
        self.assertIn("RuntimeError", record.getMessage())

    def test_unexpected_exception_still_returns_an_operation_outcome(self):
        response = fhir_api_exception_handler(RuntimeError("boom"), fhir_context())

        self.assertEqual(status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        self.assertIn("issue", response.data)

    def test_client_errors_are_not_logged_as_server_faults(self):
        logger_name = "api_fhir_r4.exceptions.fhir_api_exception_handler"
        for exc in (
            FHIRException("bad resource"),
            exceptions.NotAuthenticated(),
            exceptions.PermissionDenied(),
        ):
            with self.subTest(type(exc).__name__):
                with self.assertNoLogs(logger_name, level=logging.ERROR):
                    fhir_api_exception_handler(exc, fhir_context())

    def test_non_fhir_paths_are_left_alone(self):
        response = fhir_api_exception_handler(
            FHIRException("bad"), fhir_context("/api/graphql")
        )

        # Untouched by the FHIR converter: no OperationOutcome grafted on.
        self.assertNotIn("issue", response.data or {})


class FHIRExceptionResponseStatusTest(TestCase):
    """The status the handler actually returns, end to end through DRF."""

    def test_fhir_exception_response_is_a_client_error(self):
        response = fhir_api_exception_handler(
            FHIRRequestProcessException(["missing name"]), fhir_context()
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("issue", response.data)
