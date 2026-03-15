"""create_hotel.py"""
from dataclasses import dataclass, field
from typing import List
from app.modules.hotel.domain.entities.hotel import Hotel
from app.modules.hotel.domain.repositories.hotel_repository import HotelRepository
from app.shared.domain.base_use_case import BaseUseCase


@dataclass
class CreateHotelInput:
    owner_id:    str
    name:        str
    description: str
    address:     str
    city:        str
    country:     str
    stars:       int
    latitude:    float     = 0.0
    longitude:   float     = 0.0
    phone:       str       = ""
    email:       str       = ""
    website:     str       = ""
    amenities:   List[str] = field(default_factory=list)
    images:      List[str] = field(default_factory=list)


class CreateHotelUseCase(BaseUseCase[CreateHotelInput, Hotel]):
    def __init__(self, repository: HotelRepository):
        self.repository = repository

    def execute(self, i: CreateHotelInput) -> Hotel:
        hotel = Hotel(
            owner_id=i.owner_id, name=i.name, description=i.description,
            address=i.address, city=i.city, country=i.country, stars=i.stars,
            latitude=i.latitude, longitude=i.longitude,
            phone=i.phone, email=i.email, website=i.website,
            amenities=i.amenities, images=i.images,
        )
        return self.repository.save(hotel)
