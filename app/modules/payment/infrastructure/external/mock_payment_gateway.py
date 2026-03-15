"""
app/modules/payment/infrastructure/external/mock_payment_gateway.py
Gateway de paiement simulé — simule succès/échec sans appel réseau.
En production : remplacer par StripeGateway, PayPalGateway, etc.
"""
import logging
import random
import uuid
from abc import ABC, abstractmethod

from decouple import config

logger = logging.getLogger("app")


class PaymentGateway(ABC):
    """Interface — le domaine dépend de ce contrat."""

    @abstractmethod
    def charge(self, amount: float, currency: str, method: str, metadata: dict) -> dict:
        """
        Retourne {'success': bool, 'gateway_ref': str, 'error': str|None}
        """
        ...

    @abstractmethod
    def refund(self, gateway_ref: str, amount: float) -> dict:
        ...


class MockPaymentGateway(PaymentGateway):
    """
    Simule un gateway de paiement.
    Taux de succès configurable via MOCK_PAYMENT_SUCCESS_RATE (défaut 95%).
    """

    def __init__(self):
        self.success_rate = config("MOCK_PAYMENT_SUCCESS_RATE", default=0.95, cast=float)

    def charge(self, amount: float, currency: str, method: str, metadata: dict) -> dict:
        is_success = random.random() < self.success_rate
        ref = f"MOCK-{uuid.uuid4().hex[:12].upper()}"

        if is_success:
            logger.info(f"[MOCK PAYMENT] ✓ {amount} {currency} | ref={ref}")
            return {"success": True, "gateway_ref": ref, "error": None}
        else:
            reason = random.choice([
                "Fonds insuffisants",
                "Carte expirée",
                "Transaction refusée par la banque",
            ])
            logger.warning(f"[MOCK PAYMENT] ✗ {amount} {currency} | reason={reason}")
            return {"success": False, "gateway_ref": "", "error": reason}

    def refund(self, gateway_ref: str, amount: float) -> dict:
        ref = f"REFUND-{uuid.uuid4().hex[:12].upper()}"
        logger.info(f"[MOCK REFUND] ✓ {amount} | original_ref={gateway_ref} | refund_ref={ref}")
        return {"success": True, "gateway_ref": ref, "error": None}
