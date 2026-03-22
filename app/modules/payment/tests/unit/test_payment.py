"""
Tests unitaires Payment — entité + use cases.
pytest app/modules/payment/tests/unit/ -v
"""
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import (
    AuthorizationError,
    EntityNotFoundError,
    PaymentError,
)
from app.modules.booking.domain.entities.booking import BookingStatus
from app.modules.payment.domain.entities.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.modules.payment.domain.use_cases.process_payment import (
    GetPaymentInput,
    GetPaymentUseCase,
    ProcessPaymentInput,
    ProcessPaymentUseCase,
    RefundPaymentInput,
    RefundPaymentUseCase,
)


# ── Factories 

def _payment(
    status: PaymentStatus = PaymentStatus.SUCCEEDED,
    user_id: str = "uid-1",
    amount: float = 450.0,
    gateway_ref: str = "MOCK-ABC123",
) -> Payment:
    """Crée un Payment sans passer par __init__ pour éviter les validations."""
    p = Payment.__new__(Payment)
    for k, v in dict(
        id="pay-1", booking_id="bid-1", user_id=user_id,
        amount=amount, currency="EUR",
        status=status, method=PaymentMethod.CARD,
        gateway_ref=gateway_ref, failure_reason="",
        refunded_at=None,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        _events=[],
    ).items():
        object.__setattr__(p, k, v)
    return p


def _booking(user_id="uid-1", total_price=450.0, status=BookingStatus.PENDING):
    """Mock d'une réservation."""
    b = MagicMock()
    b.id         = "bid-1"
    b.user_id    = user_id
    b.total_price = total_price
    b.currency   = "EUR"
    b.status     = status
    return b


# Payment entity

class TestPaymentEntity:

    def test_initial_status_is_pending(self):
        p = Payment(booking_id="bid-1", user_id="uid-1", amount=100.0)
        assert p.status == PaymentStatus.PENDING

    def test_mark_succeeded(self):
        p = _payment(status=PaymentStatus.PENDING, gateway_ref="")
        p.mark_succeeded("MOCK-XYZ789")
        assert p.status      == PaymentStatus.SUCCEEDED
        assert p.gateway_ref == "MOCK-XYZ789"

    def test_mark_failed(self):
        p = _payment(status=PaymentStatus.PENDING, gateway_ref="")
        p.mark_failed("Fonds insuffisants")
        assert p.status         == PaymentStatus.FAILED
        assert p.failure_reason == "Fonds insuffisants"

    def test_refund_succeeded_payment(self):
        p = _payment(status=PaymentStatus.SUCCEEDED)
        p.refund()
        assert p.status      == PaymentStatus.REFUNDED
        assert p.refunded_at is not None

    def test_refund_non_succeeded_raises(self):
        """Seul un paiement SUCCEEDED peut être remboursé."""
        for bad_status in [PaymentStatus.PENDING, PaymentStatus.FAILED, PaymentStatus.REFUNDED]:
            p = _payment(status=bad_status)
            with pytest.raises(Exception):
                p.refund()


    def test_payment_methods(self):
        assert PaymentMethod.CARD.value           == "CARD"
        assert PaymentMethod.PAYPAL.value         == "PAYPAL"
        assert PaymentMethod.BANK_TRANSFER.value  == "BANK_TRANSFER"

    def test_payment_statuses(self):
        assert PaymentStatus.PENDING.value   == "PENDING"
        assert PaymentStatus.SUCCEEDED.value == "SUCCEEDED"
        assert PaymentStatus.FAILED.value    == "FAILED"
        assert PaymentStatus.REFUNDED.value  == "REFUNDED"


# ProcessPaymentUseCase

class TestProcessPaymentUseCase:

    def _uc(self, booking=None, gateway_success=True, gateway_error="Échec"):
        payment_repo  = MagicMock()
        booking_repo  = MagicMock()
        gateway       = MagicMock()

        booking_repo.find_by_id.return_value = booking or _booking()
        payment_repo.save.side_effect        = lambda p: p

        if gateway_success:
            gateway.charge.return_value = {
                "success": True, "gateway_ref": "MOCK-OK123", "error": None,
            }
        else:
            gateway.charge.return_value = {
                "success": False, "gateway_ref": "", "error": gateway_error,
            }

        return ProcessPaymentUseCase(payment_repo, booking_repo, gateway), payment_repo, booking_repo, gateway

    def test_successful_payment_returns_succeeded_status(self):
        uc, _, _, _ = self._uc()
        result = uc.execute(ProcessPaymentInput(booking_id="bid-1", user_id="uid-1"))
        assert result.status      == PaymentStatus.SUCCEEDED
        assert result.gateway_ref == "MOCK-OK123"

    def test_successful_payment_confirms_booking(self):
        booking = _booking()
        uc, _, booking_repo, _ = self._uc(booking=booking)
        uc.execute(ProcessPaymentInput(booking_id="bid-1", user_id="uid-1"))
        # La réservation doit être sauvegardée après confirmation
        booking_repo.save.assert_called_once()

    def test_payment_saved_to_repository(self):
        uc, payment_repo, _, _ = self._uc()
        uc.execute(ProcessPaymentInput(booking_id="bid-1", user_id="uid-1"))
        payment_repo.save.assert_called_once()

    def test_booking_not_found_raises(self):
        uc, _, booking_repo, _ = self._uc()
        booking_repo.find_by_id.return_value = None
        with pytest.raises(EntityNotFoundError) as exc:
            uc.execute(ProcessPaymentInput(booking_id="ghost", user_id="uid-1"))
        assert exc.value.entity == "Booking"

    def test_other_user_cannot_pay(self):
        """Un utilisateur ne peut pas payer la réservation d'un autre."""
        booking = _booking(user_id="uid-owner")
        uc, _, _, _ = self._uc(booking=booking)
        with pytest.raises(AuthorizationError):
            uc.execute(ProcessPaymentInput(booking_id="bid-1", user_id="uid-stranger"))


    def test_failed_payment_not_saved(self):
        """En cas d'échec, le paiement ne doit PAS être sauvegardé."""
        uc, payment_repo, _, _ = self._uc(gateway_success=False)
        with pytest.raises(PaymentError):
            uc.execute(ProcessPaymentInput(booking_id="bid-1", user_id="uid-1"))
        payment_repo.save.assert_not_called()

    def test_card_method_by_default(self):
        uc, _, _, gateway = self._uc()
        uc.execute(ProcessPaymentInput(booking_id="bid-1", user_id="uid-1"))
        call_args = gateway.charge.call_args
        assert call_args.kwargs["method"] == "CARD"

    def test_custom_payment_method(self):
        uc, _, _, gateway = self._uc()
        uc.execute(ProcessPaymentInput(booking_id="bid-1", user_id="uid-1", method="PAYPAL"))
        call_args = gateway.charge.call_args
        assert call_args.kwargs["method"] == "PAYPAL"


# GetPaymentUseCase

class TestGetPaymentUseCase:

    def test_owner_can_get_payment(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _payment(user_id="uid-1")
        uc = GetPaymentUseCase(repo)
        result = uc.execute(GetPaymentInput(payment_id="pay-1", requester_id="uid-1"))
        assert result.id == "pay-1"


    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        uc = GetPaymentUseCase(repo)
        with pytest.raises(EntityNotFoundError) as exc:
            uc.execute(GetPaymentInput(payment_id="ghost", requester_id="uid-1"))
        assert exc.value.entity == "Payment"

# RefundPaymentUseCase

class TestRefundPaymentUseCase:

    def _uc(self, payment=None, booking=None, gateway_success=True):
        payment_repo = MagicMock()
        booking_repo = MagicMock()
        gateway      = MagicMock()

        p = payment or _payment(status=PaymentStatus.SUCCEEDED, user_id="uid-1")
        payment_repo.find_by_booking.return_value = [p]
        payment_repo.save.side_effect = lambda x: x
        booking_repo.find_by_id.return_value = booking or _booking(status=BookingStatus.CONFIRMED)

        if gateway_success:
            gateway.refund.return_value = {"success": True, "gateway_ref": "REFUND-XYZ", "error": None}
        else:
            gateway.refund.return_value = {"success": False, "gateway_ref": "", "error": "Erreur"}

        return RefundPaymentUseCase(payment_repo, booking_repo, gateway), payment_repo, booking_repo

    def test_owner_can_refund(self):
        uc, _, _ = self._uc()
        result = uc.execute(RefundPaymentInput(booking_id="bid-1", requester_id="uid-1"))
        assert result.status == PaymentStatus.REFUNDED

    def test_admin_can_refund_any(self):
        p = _payment(status=PaymentStatus.SUCCEEDED, user_id="uid-owner")
        uc, _, _ = self._uc(payment=p)
        result = uc.execute(RefundPaymentInput(booking_id="bid-1", requester_id="admin", is_admin=True))
        assert result.status == PaymentStatus.REFUNDED

    def test_stranger_cannot_refund(self):
        p = _payment(status=PaymentStatus.SUCCEEDED, user_id="uid-owner")
        uc, _, _ = self._uc(payment=p)
        with pytest.raises(AuthorizationError):
            uc.execute(RefundPaymentInput(booking_id="bid-1", requester_id="stranger"))


    def test_refund_cancels_booking(self):
        """Après remboursement, la réservation doit être annulée."""
        uc, _, booking_repo = self._uc()
        uc.execute(RefundPaymentInput(booking_id="bid-1", requester_id="uid-1"))
        booking_repo.save.assert_called_once()

    def test_gateway_failure_raises_payment_error(self):
        uc, _, _ = self._uc(gateway_success=False)
        with pytest.raises(PaymentError):
            uc.execute(RefundPaymentInput(booking_id="bid-1", requester_id="uid-1"))
