from unittest import mock

from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APITestCase

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import GenericFhirAPITestMixin, FhirApiReadTestMixin
from api_fhir_r4.tests.mixin.invoiceTestMixin import InvoiceTestMixin
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from insuree.models import Insuree
from policy.test_helpers import create_test_policy2
from product.test_helpers import create_test_product


class InvoiceAPITests(
    GenericFhirAPITestMixin,
    FhirApiReadTestMixin,
    APITestCase,
    LogInMixin,
    InvoiceTestMixin,
):
    base_url = GeneralConfiguration.get_base_url() + "Invoice/?resourceType=invoice"
    _test_json_path = "/test/test_invoice.json"

    def setUp(self):
        super(InvoiceAPITests, self).setUp()
        user = self.get_or_create_user_api()
        self.imis_invoice, self.imis_invoice_line_item = (
            self.create_test_imis_instance()
        )
        self.imis_invoice.thirdparty = Insuree.objects.first()
        self.imis_invoice.save(username=user.username)
        self.imis_invoice_line_item.save(username=user.username)


class InvoiceListRobustnessAPITests(
    GenericFhirAPITestMixin,
    APITestCase,
    LogInMixin,
    InvoiceTestMixin,
):
    """
    OP-3254: the invoice list hid nothing soft-deleted, and one invoice that can't be
    converted (an invoice for a policy, whose type isn't mapped) failed the whole list.
    """
    base_url = GeneralConfiguration.get_base_url() + "Invoice/?resourceType=invoice"

    def setUp(self):
        super().setUp()
        self.user = self.get_or_create_user_api()
        self.live = self._invoice("OP3254-LIVE")
        self.deleted = self._invoice("OP3254-DEL")
        self.deleted.is_deleted = True
        self.deleted.save(username=self.user.username)

    def _invoice(self, code, subject=None):
        invoice, line_item = self.create_test_imis_instance()
        invoice.code = code
        # Invoices are scoped through their subject (row_scope): without one the
        # list never shows them.
        subject = subject or self.test_insuree.family
        invoice.subject_type = ContentType.objects.get_for_model(subject)
        invoice.subject_id = subject.id
        invoice.thirdparty = Insuree.objects.first()
        invoice.save(username=self.user.username)
        line_item.invoice = invoice
        line_item.save(username=self.user.username)
        return invoice

    def _entries(self, url):
        self.login()
        response = self.client.get(url, data=None, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, str(response.content)[:300])
        body = response.json()
        return body, [entry["resource"] for entry in body.get("entry", [])]

    @staticmethod
    def _codes(resources):
        return {
            identifier.get("value")
            for resource in resources
            for identifier in resource.get("identifier", [])
        }

    def test_soft_deleted_invoices_are_hidden_by_default(self):
        body, resources = self._entries(self.base_url + "&_count=100")
        self.assertIn("OP3254-LIVE", self._codes(resources))
        self.assertNotIn("OP3254-DEL", self._codes(resources))

    def test_soft_deleted_invoices_are_listed_with_is_deleted_true(self):
        body, resources = self._entries(self.base_url + "&isDeleted=true&_count=100")
        self.assertIn("OP3254-DEL", self._codes(resources))
        self.assertNotIn("OP3254-LIVE", self._codes(resources))

    def test_an_invoice_that_cannot_be_converted_does_not_fail_the_list(self):
        broken = self._invoice("OP3254-POL", subject=create_test_policy2(
            create_test_product("OP3254P"), self.test_insuree)[0])
        with mock.patch("api_fhir_r4.serializers.baseSerializer.capture_exception", create=True) as capture:
            body, resources = self._entries(self.base_url + "&_count=100")

        self.assertIn("OP3254-LIVE", self._codes(resources))
        outcomes = [r for r in resources if r["resourceType"] == "OperationOutcome"]
        self.assertEqual(len(outcomes), 1, resources)
        self.assertEqual(outcomes[0]["id"], str(broken.pk))
        self.assertIn(str(broken.pk), outcomes[0]["issue"][0]["details"]["text"])
        # still counted: the entry is rendered as an outcome, not dropped
        self.assertEqual(body["total"], len(resources))
        capture.assert_called_once()
