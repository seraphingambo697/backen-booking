from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from app.core.exceptions import DomainValidationError
from app.shared.domain.base_entity import BaseEntity


class PaymentStatus(str, Enum):
    PENDING   = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED    = "FAILED"
    REFUNDED  = "REFUNDED"


class PaymentMethod(str, Enum):
    CARD        = "CARD"
    PAYPAL      = "PAYPAL"
    BANK_TRANSFER = "BANK_TRANSFER"


@dataclass
class Payment(BaseEntity):
    booking_id:      str           = ""
    user_id:         str           = ""
    amount:          float         = 0.0
    currency:        str           = "EUR"
    status:          PaymentStatus = PaymentStatus.PENDING
    method:          PaymentMethod = PaymentMethod.CARD
    gateway_ref:     str           = ""   # Référence côté gateway (mock: "MOCK-xxxx")
    failure_reason:  str           = ""
    refunded_at:     Optional[datetime] = None

    def mark_succeeded(self, gateway_ref: str):
        self.status      = PaymentStatus.SUCCEEDED
        self.gateway_ref = gateway_ref
        self.touch()

    def mark_failed(self, reason: str):
        self.status         = PaymentStatus.FAILED
        self.failure_reason = reason
        self.touch()

    def refund(self):
        if self.status != PaymentStatus.SUCCEEDED:
            raise DomainValidationError("status", "Seul un paiement réussi peut être remboursé.")
        self.status      = PaymentStatus.REFUNDED
        self.refunded_at = datetime.utcnow()
        self.touch()
