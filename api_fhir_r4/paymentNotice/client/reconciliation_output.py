from dataclasses import dataclass
from fhir.resources.paymentreconciliation import PaymentReconciliation
from typing import Any


@dataclass
class ReconciliationOutput:
    reconciliation_id: str
    reconciliation_success: bool
    reason_of_failure: Any = None
    payment_reconciliation: PaymentReconciliation = None
