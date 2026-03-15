"""
app/modules/booking/domain/use_cases/get_booking.py
Lecture des réservations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.core.exceptions import AuthorizationError, EntityNotFoundError
from app.modules.booking.domain.entities.booking import Booking, BookingStatus
from app.modules.booking.domain.repositories.booking_repository import BookingRepository
from app.shared.domain.base_use_case import BaseUseCase


@dataclass
class GetBookingInput:
    booking_id:   str
    requester_id: str
    is_admin:     bool = False


@dataclass
class ListBookingsInput:
    user_id: str
    status:  Optional[str] = None   # Filtre optionnel par statut


class GetBookingUseCase(BaseUseCase[GetBookingInput, Booking]):

    def __init__(self, repository: BookingRepository):
        self.repository = repository

    def execute(self, i: GetBookingInput) -> Booking:
        booking = self.repository.find_by_id(i.booking_id)
        if not booking:
            raise EntityNotFoundError("Booking", i.booking_id)
        if not booking.belongs_to(i.requester_id) and not i.is_admin:
            raise AuthorizationError("Cette réservation ne vous appartient pas.")
        return booking


class ListBookingsUseCase(BaseUseCase[ListBookingsInput, List[Booking]]):

    def __init__(self, repository: BookingRepository):
        self.repository = repository

    def execute(self, i: ListBookingsInput) -> List[Booking]:
        status = BookingStatus(i.status) if i.status else None
        return self.repository.find_by_user(i.user_id, status=status)
