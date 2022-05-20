import logging
import requests

from django.core.exceptions import ValidationError
from fhir.resources.paymentreconciliation import PaymentReconciliation

from .reconciliation_output import ReconciliationOutput
from api_fhir_r4.configurations import R4PaymentReconciliationConfig

logger = logging.getLogger('openIMIS')


class ReconciliationClient:
    def get_reconciliation(self,  reconciliation_id: str) -> ReconciliationOutput:
        try:
            get_args = self._get_args(reconciliation_id)
            response = requests.get(**get_args)
            status = response.status_code
            if status >= 400:
                return ReconciliationOutput(reconciliation_id, False, response)
            else:
                response = response.json()
                payment_reconciliation = PaymentReconciliation(**response)
                return ReconciliationOutput(reconciliation_id, True, None, payment_reconciliation)
        except Exception as e:
            error = F"Fetching payment reconciliation has failed due to {e}"
            logger.error(error)
            import traceback
            logger.debug(traceback.format_exc())
            return ReconciliationOutput(reconciliation_id, False, error)

    @property
    def _base_headers(self):
        return {
            'content-type': 'application/json',
            'accept': 'application/json',
            'authorization': f'{R4PaymentReconciliationConfig.get_fhir_payment_reconciliation_token()}'
        }

    def _get_args(self, reconciliation_id: str):
        reference = f'PaymentReconciliation/{reconciliation_id}/'
        url = f'{R4PaymentReconciliationConfig.get_fhir_payment_reconciliation_url()}{reference}'
        if 'http://localhost' in url or 'http://127.0.0.1' in url or \
                'https://localhost' in url or 'https://127.0.0.1' in url:
            raise ValidationError('You pointed to the same URL as this API call')
        return {
            'headers': {**self._base_headers},
            'url': f'{R4PaymentReconciliationConfig.get_fhir_payment_reconciliation_url()}{reference}',
        }
