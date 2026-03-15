"""confirm_booking.py — Confirmation d'une réservation PENDING après paiement."""
from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import AuthorizationError, EntityNotFoundError
from app.modules.booking.domain.entities.booking import Booking
from app.modules.booking.domain.repositories.booking_repository import BookingRepository
from app.shared.domain.base_use_case import BaseUseCase
from app.shared.infrastructure.database.transactional import transactional


@dataclass
class ConfirmBookingInput:
    booking_id:   str
    requester_id: str
    is_admin:     bool = False


class ConfirmBookingUseCase(BaseUseCase[ConfirmBookingInput, Booking]):
    """
    Confirme une réservation PENDING.
    Normalement appelé par ProcessPaymentUseCase après succès du paiement,
    pas directement depuis l'API publique.
    """

    def __init__(self, repository: BookingRepository):
        self.repository = repository

    @transactional
    def execute(self, i: ConfirmBookingInput) -> Booking:
        booking = self.repository.find_by_id(i.booking_id)
        if not booking:
            raise EntityNotFoundError("Booking", i.booking_id)
        if not booking.belongs_to(i.requester_id) and not i.is_admin:
            raise AuthorizationError("Cette réservation ne vous appartient pas.")
        booking.confirm()
        return self.repository.save(booking)
