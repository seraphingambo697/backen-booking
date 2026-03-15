"""
app/modules/booking/domain/use_cases/cancel_booking.py
Annulation d'une réservation avec règle d'annulation gratuite.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from app.core.exceptions import AuthorizationError, EntityNotFoundError
from app.modules.booking.domain.entities.booking import Booking
from app.modules.booking.domain.repositories.booking_repository import BookingRepository
from app.shared.domain.base_use_case import BaseUseCase
from app.shared.infrastructure.database.transactional import transactional


@dataclass
class CancelBookingInput:
    booking_id:   str
    requester_id: str
    reason:       str  = ""
    is_admin:     bool = False


@dataclass
class CancelBookingResult:
    booking:           Booking
    is_free:           bool    # Annulation gratuite ?
    refund_amount:     float   # Montant à rembourser (0 si non gratuite)
    refund_currency:   str


class CancelBookingUseCase(BaseUseCase[CancelBookingInput, CancelBookingResult]):

    def __init__(self, repository: BookingRepository):
        self.repository = repository

    @transactional
    def execute(self, i: CancelBookingInput) -> CancelBookingResult:
        booking = self.repository.find_by_id(i.booking_id)
        if not booking:
            raise EntityNotFoundError("Booking", i.booking_id)
        if not booking.belongs_to(i.requester_id) and not i.is_admin:
            raise AuthorizationError("Cette réservation ne vous appartient pas.")

        min_hours = getattr(settings, "BOOKING_FREE_CANCEL_HOURS", 48)
        is_free   = booking.is_free_cancellation(min_hours)

        # Déclenche BookingCancelled domain event + transition d'état
        booking.cancel(reason=i.reason)
        saved = self.repository.save(booking)

        refund_amount = saved.total_price if is_free else 0.0

        return CancelBookingResult(
            booking         = saved,
            is_free         = is_free,
            refund_amount   = refund_amount,
            refund_currency = saved.currency,
        )
