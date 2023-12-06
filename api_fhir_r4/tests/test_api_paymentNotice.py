import json
import os

from django.utils.translation import gettext as _
from rest_framework.test import APITestCase
from rest_framework import status

from api_fhir_r4.configurations import GeneralConfiguration
from api_fhir_r4.tests import (
    GenericFhirAPITestMixin,
    FhirApiReadTestMixin
)
from api_fhir_r4.tests.mixin.logInMixin import LogInMixin
from invoice.models import (
    Invoice,
    PaymentInvoice,
    DetailPaymentInvoice
)
from invoice.tests.helpers import create_test_invoice


class PaymentNoticeAPITests(GenericFhirAPITestMixin, FhirApiReadTestMixin, APITestCase, LogInMixin):

    base_url = GeneralConfiguration.get_base_url()+'PaymentNotice/'
    _test_json_path = "/test/test_payment_notice.json"
    _test_invoice_uuid = "bd84b2f2-ec1d-48de-8f8c-5a477aa4a29f"
    _test_json_path_credentials = "/test/test_login.json"
    _test_request_data_credentials = None
    _user = None

    def setUp(self):
        super(PaymentNoticeAPITests, self).setUp()
        self._user = self.get_or_create_user_api()

    def create_dependencies(self):
        invoice = create_test_invoice(subject=None, thirdparty=None, user=self._user, **{
            'id': self._test_invoice_uuid,
            'amount_total': '10000.0',
            'amount_net': '10000.0',
            'user_created': self._user,
            'user_updated': self._user
        })
        return invoice

    def _update_payload_wrong_status(self, data):
        data["status"] = 'activeee'
        return data

    def _update_payload_wrong_payment_status(self, data):
        data["paymentStatus"]['coding'][0]['code'] = 'cleatedddd'
        return data

    def _update_payload_wrong_request_type(self, data):
        data["request"]['type'] = 'Invoices'
        return data

    def test_post_should_create_correctly(self):
        invoice = self.create_dependencies()
        headers = self.initialize_auth()
        response = self.client.post(self.base_url, data=self._test_request_data, format='json', **headers)
        if response.status_code == status.HTTP_201_CREATED:
            response_json_payment = response.json()
            payment_id = response_json_payment['id']
            DetailPaymentInvoice.objects.filter(payment__id=payment_id).delete()
            PaymentInvoice.objects.filter(id=payment_id).delete()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.content)
        Invoice.objects.filter(id=invoice.id).delete()

    def test_post_wrong_status(self):
        invoice = self.create_dependencies()
        headers = self.initialize_auth()
        modified_payload = self._update_payload_wrong_status(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json', **headers)
        response_json_no_name = response.json()
        self.assertEqual(
            self.get_response_details(response_json_no_name),
            _("The request cannot be processed due to the following issues:\nBad value "
              "in paymentStatus, should be either 'active', 'cancelled', draft', 'entered-in-error'"
              ",\nBad value in paymentStatus, ""should be either 'active', 'cancelled', draft', 'entered-in-error'")
        )
        Invoice.objects.filter(id=invoice.id).delete()

    def test_post_wrong_payment_status(self):
        invoice = self.create_dependencies()
        headers = self.initialize_auth()
        modified_payload = self._update_payload_wrong_payment_status(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json', **headers)
        response_json_no_name = response.json()
        self.assertEqual(
            self.get_response_details(response_json_no_name),
            _("The request cannot be processed due to the following "
              "issues:\nBad value in paymentStatus, should be either 'paid' or 'cleared'")
        )
        Invoice.objects.filter(id=invoice.id).delete()

    def test_post_wrong_request_type(self):
        invoice = self.create_dependencies()
        headers = self.initialize_auth()
        modified_payload = self._update_payload_wrong_request_type(data=self._test_request_data)
        response = self.client.post(self.base_url, data=modified_payload, format='json', **headers)
        response_json_no_name = response.json()
        self.assertEqual(
            self.get_response_details(response_json_no_name),
            _("The request cannot be processed due to the following "
              "issues:\nBad value in type in request, should be either 'bill' or 'invoice'")
        )
        Invoice.objects.filter(id=invoice.id).delete()
