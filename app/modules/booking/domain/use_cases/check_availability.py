"""check_availability.py — Chambres disponibles pour un hôtel/dates/voyageurs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List

from app.modules.booking.domain.repositories.booking_repository import BookingRepository
from app.modules.hotel.domain.entities.hotel import Room
from app.modules.hotel.domain.repositories.hotel_repository import RoomRepository
from app.shared.domain.base_use_case import BaseUseCase
from app.shared.domain.value_objects import DateRange, GuestCount, Money


@dataclass
class CheckAvailabilityInput:
    hotel_id:    str
    check_in:    date
    check_out:   date
    guest_count: int = 1
    adults:      int = 0
    children:    int = 0


@dataclass
class AvailableRoom:
    """DTO : chambre + prix calculé pour le séjour."""
    room:           Room
    nights:         int
    total_price:    float
    currency:       str
    is_free_cancel: bool


class CheckAvailabilityUseCase(BaseUseCase[CheckAvailabilityInput, List[AvailableRoom]]):

    def __init__(self, booking_repo: BookingRepository, room_repo: RoomRepository):
        self.booking_repo = booking_repo
        self.room_repo    = room_repo

    def execute(self, i: CheckAvailabilityInput) -> List[AvailableRoom]:
        date_range = DateRange(check_in=i.check_in, check_out=i.check_out)
        adults   = i.adults if i.adults > 0 else i.guest_count
        children = i.children if i.children > 0 else 0
        guests   = GuestCount(adults=adults, children=children)

        rooms = self.room_repo.find_available_rooms(
            hotel_id    = i.hotel_id,
            check_in    = i.check_in,
            check_out   = i.check_out,
            guest_count = guests.total,
        )

        results = []
        for room in rooms:
            total = Money.from_price_per_night(room.price_per_night, date_range.nights, room.currency)
            results.append(AvailableRoom(
                room           = room,
                nights         = date_range.nights,
                total_price    = total.amount,
                currency       = total.currency,
                is_free_cancel = date_range.is_free_cancellation(),
            ))
        return results
