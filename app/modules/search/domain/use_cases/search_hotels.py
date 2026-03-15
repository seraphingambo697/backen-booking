"""
app/modules/search/domain/use_cases/search_hotels.py
Recherche d'hôtels avec filtres : ville, dates, voyageurs, étoiles, prix max.
"""
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.modules.booking.domain.repositories.booking_repository import BookingRepository
from app.modules.hotel.domain.entities.hotel import Hotel, Room
from app.modules.hotel.domain.repositories.hotel_repository import HotelRepository, RoomRepository
from app.shared.domain.base_use_case import BaseUseCase


@dataclass
class SearchHotelsInput:
    city:        str
    check_in:    date
    check_out:   date
    guest_count: int  = 1
    stars_min:   Optional[int]   = None
    price_max:   Optional[float] = None
    amenities:   Optional[List[str]] = None


@dataclass
class HotelSearchResult:
    hotel:           Hotel
    available_rooms: List[Room]
    min_price:       float
    avg_rating:      float = 0.0


class SearchHotelsUseCase(BaseUseCase[SearchHotelsInput, List[HotelSearchResult]]):
    """
    Recherche multi-critères.
    Retourne uniquement les hôtels avec au moins une chambre disponible.
    """

    def __init__(self, hotel_repo: HotelRepository, room_repo: RoomRepository, booking_repo: BookingRepository):
        self.hotel_repo   = hotel_repo
        self.room_repo    = room_repo
        self.booking_repo = booking_repo

    def execute(self, i: SearchHotelsInput) -> List[HotelSearchResult]:
        # 1. Hôtels dans la ville demandée
        hotels = self.hotel_repo.find_by_city(i.city)

        # 2. Filtre étoiles
        if i.stars_min:
            hotels = [h for h in hotels if h.stars >= i.stars_min]

        # 3. Filtre équipements
        if i.amenities:
            hotels = [h for h in hotels
                      if all(a in h.amenities for a in i.amenities)]

        results = []
        for hotel in hotels:
            # 4. Chambres disponibles pour les dates + capacité
            available_rooms = self.room_repo.find_available_rooms(
                hotel.id, i.check_in, i.check_out, i.guest_count
            )
            if not available_rooms:
                continue

            # 5. Filtre prix max
            if i.price_max:
                available_rooms = [r for r in available_rooms if r.price_per_night <= i.price_max]
            if not available_rooms:
                continue

            min_price = min(r.price_per_night for r in available_rooms)
            results.append(HotelSearchResult(
                hotel=hotel,
                available_rooms=available_rooms,
                min_price=min_price,
            ))

        # 6. Tri par prix croissant
        results.sort(key=lambda r: r.min_price)
        return results
