"""Payment use cases"""
from dataclasses import dataclass
from typing import Optional

from app.core.exceptions import EntityNotFoundError, PaymentError, AuthorizationError
from app.modules.booking.domain.repositories.booking_repository import BookingRepository
from app.modules.payment.domain.entities.payment import Payment, PaymentMethod, PaymentStatus
from app.modules.payment.infrastructure.external.mock_payment_gateway import PaymentGateway
from app.shared.domain.base_use_case import BaseUseCase


class PaymentRepository:
    """Interface simplifiée — implémentée dans infrastructure."""
    def save(self, p): ...
    def find_by_id(self, id): ...
    def find_by_booking(self, booking_id): ...


# ── ProcessPayment ──────
@dataclass
class ProcessPaymentInput:
    booking_id: str
    user_id:    str
    method:     str = "CARD"

class ProcessPaymentUseCase(BaseUseCase[ProcessPaymentInput, Payment]):
    def __init__(self, payment_repo, booking_repo: BookingRepository, gateway: PaymentGateway):
        self.payment_repo = payment_repo
        self.booking_repo = booking_repo
        self.gateway      = gateway

    def execute(self, i: ProcessPaymentInput) -> Payment:
        booking = self.booking_repo.find_by_id(i.booking_id)
        if not booking:
            raise EntityNotFoundError("Booking", i.booking_id)
        if booking.user_id != i.user_id:
            raise AuthorizationError("Cette réservation ne vous appartient pas.")

        payment = Payment(
            booking_id=i.booking_id,
            user_id=i.user_id,
            amount=booking.total_price,
            currency=booking.currency,
            method=PaymentMethod(i.method),
        )

        result = self.gateway.charge(
            amount=payment.amount,
            currency=payment.currency,
            method=payment.method.value,
            metadata={"booking_id": i.booking_id, "user_id": i.user_id},
        )

        if result["success"]:
            payment.mark_succeeded(result["gateway_ref"])
            booking.confirm()
            self.booking_repo.save(booking)
        else:
            payment.mark_failed(result["error"])
            raise PaymentError(result["error"])

        return self.payment_repo.save(payment)


# ── GetPayment ──────────
@dataclass
class GetPaymentInput:
    payment_id:   str
    requester_id: str

class GetPaymentUseCase(BaseUseCase[GetPaymentInput, Payment]):
    def __init__(self, repository):
        self.repository = repository
    def execute(self, i: GetPaymentInput) -> Payment:
        p = self.repository.find_by_id(i.payment_id)
        if not p: raise EntityNotFoundError("Payment", i.payment_id)
        if p.user_id != i.requester_id:
            raise AuthorizationError("Ce paiement ne vous appartient pas.")
        return p


# ── RefundPayment ───────
@dataclass
class RefundPaymentInput:
    booking_id:   str
    requester_id: str
    is_admin:     bool = False

class RefundPaymentUseCase(BaseUseCase[RefundPaymentInput, Payment]):
    def __init__(self, payment_repo, booking_repo: BookingRepository, gateway: PaymentGateway):
        self.payment_repo = payment_repo
        self.booking_repo = booking_repo
        self.gateway      = gateway

    def execute(self, i: RefundPaymentInput) -> Payment:
        payments = self.payment_repo.find_by_booking(i.booking_id)
        payment = next((p for p in payments if p.status == PaymentStatus.SUCCEEDED), None)
        if not payment:
            raise EntityNotFoundError("Payment réussi pour booking", i.booking_id)
        if payment.user_id != i.requester_id and not i.is_admin:
            raise AuthorizationError("Action non autorisée.")

        result = self.gateway.refund(payment.gateway_ref, payment.amount)
        if not result["success"]:
            raise PaymentError("Échec du remboursement.")

        payment.refund()
        booking = self.booking_repo.find_by_id(i.booking_id)
        if booking:
            booking.cancel(reason="Remboursé")
            self.booking_repo.save(booking)

        return self.payment_repo.save(payment)
