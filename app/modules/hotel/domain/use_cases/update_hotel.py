"""update_hotel.py"""
from dataclasses import dataclass, field
from typing import List, Optional
from app.core.exceptions import AuthorizationError, EntityNotFoundError
from app.modules.hotel.domain.entities.hotel import Hotel
from app.modules.hotel.domain.repositories.hotel_repository import HotelRepository
from app.shared.domain.base_use_case import BaseUseCase


@dataclass
class UpdateHotelInput:
    hotel_id:     str
    requester_id: str
    is_admin:     bool             = False
    name:         Optional[str]    = None
    description:  Optional[str]    = None
    address:      Optional[str]    = None
    city:         Optional[str]    = None
    country:      Optional[str]    = None
    stars:        Optional[int]    = None
    phone:        Optional[str]    = None
    email:        Optional[str]    = None
    website:      Optional[str]    = None
    amenities:    Optional[List[str]] = None
    images:       Optional[List[str]] = None


class UpdateHotelUseCase(BaseUseCase[UpdateHotelInput, Hotel]):
    def __init__(self, repository: HotelRepository):
        self.repository = repository

    def execute(self, i: UpdateHotelInput) -> Hotel:
        hotel = self.repository.find_by_id(i.hotel_id)
        if not hotel:
            raise EntityNotFoundError("Hotel", i.hotel_id)
        if not hotel.is_owned_by(i.requester_id) and not i.is_admin:
            raise AuthorizationError("Vous n'êtes pas propriétaire de cet hôtel.")

        _FIELDS = ("name","description","address","city","country","stars",
                   "phone","email","website","amenities","images")
        for attr in _FIELDS:
            val = getattr(i, attr)
            if val is not None:
                setattr(hotel, attr, val)
        hotel.touch()
        return self.repository.save(hotel)
