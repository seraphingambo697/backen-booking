from __future__ import annotations
from abc import abstractmethod
from datetime import date
from typing import List, Optional
from app.modules.hotel.domain.entities.hotel import Hotel, Room
from app.shared.domain.base_repository import BaseRepository


class HotelRepository(BaseRepository[Hotel]):
    @abstractmethod
    def find_all(self, city: Optional[str] = None, active_only: bool = True) -> List[Hotel]: ...
    @abstractmethod
    def find_by_city(self, city: str) -> List[Hotel]: ...
    @abstractmethod
    def find_by_owner(self, owner_id: str) -> List[Hotel]: ...
    @abstractmethod
    def search(self, city: str, stars_min: Optional[int] = None,
               amenities: Optional[List[str]] = None, active_only: bool = True) -> List[Hotel]: ...


class RoomRepository(BaseRepository[Room]):
    @abstractmethod
    def find_by_hotel(self, hotel_id: str, available_only: bool = False) -> List[Room]: ...
    @abstractmethod
    def find_available_rooms(self, hotel_id: str, check_in: date,
                             check_out: date, guest_count: int) -> List[Room]: ...
    @abstractmethod
    def find_by_type(self, hotel_id: str, room_type: str) -> List[Room]: ...
