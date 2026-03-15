"""
app/shared/infrastructure/external/base_gateway.py
Interface abstraite pour tous les gateways vers des services externes.

Principe : le domaine dépend de cette interface, jamais des SDKs tiers.
Cela permet de swapper Stripe → PayPal, SendGrid → SES etc.
sans toucher au moindre use case.

Gateways actuels :
  - PaymentGateway  (mock/Stripe/PayPal)  → modules/payment/
  - NotificationGateway (email/SMS)        → à implémenter
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("app")


# ── Résultat standard ───

@dataclass
class GatewayResult:
    """
    Résultat uniforme retourné par tous les gateways.

    success=True  → operation_id contient la référence externe
    success=False → error_code + error_message décrivent le problème
    """
    success:      bool
    operation_id: str        = ""   # Référence côté provider (ex: "pi_3N…" pour Stripe)
    error_code:   str        = ""
    error_message: str       = ""
    raw:          Any        = None  # Réponse brute du provider (pour le debug)

    @classmethod
    def ok(cls, operation_id: str, raw: Any = None) -> "GatewayResult":
        return cls(success=True, operation_id=operation_id, raw=raw)

    @classmethod
    def fail(cls, error_code: str, error_message: str, raw: Any = None) -> "GatewayResult":
        return cls(success=False, error_code=error_code, error_message=error_message, raw=raw)

    def __bool__(self) -> bool:
        return self.success


# ── Interface Payment Gateway ─────────────────────────────────────────────────

class PaymentGateway(ABC):
    """
    Contrat pour les gateways de paiement.
    Implémentations : MockPaymentGateway, StripeGateway, PayPalGateway.
    """

    @abstractmethod
    def charge(
        self,
        amount:   float,
        currency: str,
        method:   str,
        metadata: dict,
    ) -> GatewayResult:
        """
        Débite le montant.

        Args:
            amount:   Montant en unité principale (ex: 150.00 pour 150€)
            currency: Code ISO 4217 (ex: "EUR", "USD")
            method:   Méthode de paiement ("CARD", "PAYPAL"…)
            metadata: Données contextuelles (booking_id, user_id…)

        Returns:
            GatewayResult.ok(operation_id)  si succès
            GatewayResult.fail(code, msg)   si échec
        """
        ...

    @abstractmethod
    def refund(
        self,
        operation_id: str,
        amount:       float,
        reason:       str = "",
    ) -> GatewayResult:
        """
        Rembourse un paiement existant.

        Args:
            operation_id: Référence de la transaction originale
            amount:       Montant à rembourser (partiel possible)
            reason:       Motif du remboursement
        """
        ...


# ── Interface Notification Gateway ────────────────────────────────────────────

class NotificationGateway(ABC):
    """
    Contrat pour les gateways de notification (email, SMS).
    Implémentations : ConsoleNotificationGateway, SendGridGateway, TwilioGateway.
    """

    @abstractmethod
    def send_email(
        self,
        to:       str,
        subject:  str,
        template: str,
        context:  dict,
    ) -> GatewayResult:
        """Envoie un email. template = slug du template (ex: 'booking_confirmed')."""
        ...

    @abstractmethod
    def send_sms(
        self,
        to:      str,
        message: str,
    ) -> GatewayResult:
        """Envoie un SMS."""
        ...
