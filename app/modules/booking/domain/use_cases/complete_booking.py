"""complete_booking.py — Marquer une réservation comme terminée (check-out)."""
from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import EntityNotFoundError
from app.modules.booking.domain.entities.booking import Booking
from app.modules.booking.domain.repositories.booking_repository import BookingRepository
from app.shared.domain.base_use_case import BaseUseCase
from app.shared.infrastructure.database.transactional import transactional


@dataclass
class CompleteBookingInput:
    booking_id: str
    is_admin:   bool = True


class CompleteBookingUseCase(BaseUseCase[CompleteBookingInput, Booking]):
    """Transition CONFIRMED → COMPLETED. Appelé par admin ou cron de check-out."""

    def __init__(self, repository: BookingRepository):
        self.repository = repository

    @transactional
    def execute(self, i: CompleteBookingInput) -> Booking:
        booking = self.repository.find_by_id(i.booking_id)
        if not booking:
            raise EntityNotFoundError("Booking", i.booking_id)
        booking.complete()
        return self.repository.save(booking)
