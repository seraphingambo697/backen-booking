"""
app/modules/booking/domain/repositories/booking_repository.py
Interface repository Booking — contrat abstrait, zéro Django.
"""
from __future__ import annotations

from abc import abstractmethod
from datetime import date
from typing import List, Optional

from app.modules.booking.domain.entities.booking import Booking, BookingStatus
from app.shared.domain.base_repository import BaseRepository


class BookingRepository(BaseRepository[Booking]):

    @abstractmethod
    def find_by_user(
        self,
        user_id: str,
        status: Optional[BookingStatus] = None,
    ) -> List[Booking]: ...

    @abstractmethod
    def find_by_hotel(
        self,
        hotel_id: str,
        status: Optional[BookingStatus] = None,
    ) -> List[Booking]: ...

    @abstractmethod
    def find_by_room_and_dates(
        self,
        room_id:   str,
        check_in:  date,
        check_out: date,
    ) -> List[Booking]:
        """Retourne les réservations CONFIRMED/PENDING qui chevauchent la plage donnée."""
        ...

    @abstractmethod
    def find_active_by_room(self, room_id: str) -> List[Booking]:
        """Réservations actives (PENDING ou CONFIRMED) pour une chambre."""
        ...

    @abstractmethod
    def find_by_status(self, status: BookingStatus) -> List[Booking]: ...

    @abstractmethod
    def count_by_user(self, user_id: str) -> int: ...
