"""get_hotel.py"""
from dataclasses import dataclass
from typing import List, Optional
from app.core.exceptions import EntityNotFoundError
from app.modules.hotel.domain.entities.hotel import Hotel
from app.modules.hotel.domain.repositories.hotel_repository import HotelRepository
from app.shared.domain.base_use_case import BaseUseCase


@dataclass
class GetHotelInput:
    hotel_id: str

@dataclass
class ListHotelsInput:
    city: Optional[str] = None
    active_only: bool   = True


class GetHotelUseCase(BaseUseCase[GetHotelInput, Hotel]):
    def __init__(self, repository: HotelRepository):
        self.repository = repository

    def execute(self, i: GetHotelInput) -> Hotel:
        hotel = self.repository.find_by_id(i.hotel_id)
        if not hotel:
            raise EntityNotFoundError("Hotel", i.hotel_id)
        return hotel


class ListHotelsUseCase(BaseUseCase[ListHotelsInput, List[Hotel]]):
    def __init__(self, repository: HotelRepository):
        self.repository = repository

    def execute(self, i: ListHotelsInput) -> List[Hotel]:
        return self.repository.find_all(city=i.city, active_only=i.active_only)
