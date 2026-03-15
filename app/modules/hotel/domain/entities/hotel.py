"""
app/modules/hotel/domain/entities/hotel.py
Entités Hotel et Room — logique métier pure, sans Django.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from app.core.exceptions import DomainValidationError
from app.shared.domain.base_entity import BaseEntity


# ── Enums ───────────────

class RoomType(str, Enum):
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    TWIN   = "TWIN"
    SUITE  = "SUITE"
    DELUXE = "DELUXE"
    FAMILY = "FAMILY"

    @classmethod
    def choices(cls) -> list[str]:
        return [e.value for e in cls]


class HotelStatus(str, Enum):
    ACTIVE   = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING  = "PENDING"   # En attente de validation admin


# ── Hotel ───────────────

@dataclass
class Hotel(BaseEntity):
    name:        str              = ""
    description: str              = ""
    address:     str              = ""
    city:        str              = ""
    country:     str              = ""
    latitude:    float            = 0.0
    longitude:   float            = 0.0
    stars:       int              = 3
    amenities:   List[str]        = field(default_factory=list)
    images:      List[str]        = field(default_factory=list)
    status:      HotelStatus      = HotelStatus.ACTIVE
    owner_id:    str              = ""
    phone:       str              = ""
    email:       str              = ""
    website:     str              = ""

    def __post_init__(self):
        if self.name:   self._validate_name(self.name)
        if self.stars:  self._validate_stars(self.stars)
        if self.email:  self._validate_email(self.email)

    # ── Validations ────

    @staticmethod
    def _validate_name(name: str):
        if not (2 <= len(name.strip()) <= 200):
            raise DomainValidationError("name", "Le nom doit contenir entre 2 et 200 caractères.")

    @staticmethod
    def _validate_stars(stars: int):
        if stars not in range(1, 6):
            raise DomainValidationError("stars", "Le classement doit être entre 1 et 5 étoiles.")

    @staticmethod
    def _validate_email(email: str):
        pattern = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
        if not pattern.match(email):
            raise DomainValidationError("email", f"'{email}' n'est pas un email valide.")

    # ── Comportements ───

    @property
    def is_active(self) -> bool:
        return self.status == HotelStatus.ACTIVE

    def activate(self):
        self.status = HotelStatus.ACTIVE
        self.touch()

    def deactivate(self):
        self.status = HotelStatus.INACTIVE
        self.touch()

    def add_amenity(self, amenity: str):
        if amenity and amenity not in self.amenities:
            self.amenities.append(amenity)
            self.touch()

    def remove_amenity(self, amenity: str):
        if amenity in self.amenities:
            self.amenities.remove(amenity)
            self.touch()

    def add_image(self, url: str):
        if url and url not in self.images:
            self.images.append(url)
            self.touch()

    def compute_average_rating(self, ratings: List[float]) -> float:
        """Calcule la note moyenne à partir d'une liste de notes (1-5)."""
        if not ratings:
            return 0.0
        return round(sum(ratings) / len(ratings), 1)

    def is_owned_by(self, user_id: str) -> bool:
        return self.owner_id == user_id

    def __str__(self) -> str:
        return f"{self.name} ({self.stars}★ — {self.city})"


# ── Room ────────────────

@dataclass
class Room(BaseEntity):
    hotel_id:        str       = ""
    name:            str       = ""
    type:            RoomType  = RoomType.DOUBLE
    description:     str       = ""
    price_per_night: float     = 0.0
    currency:        str       = "EUR"
    capacity:        int       = 2
    size_sqm:        int       = 25
    bed_count:       int       = 1
    bed_type:        str       = "Double"
    floor:           int       = 0
    amenities:       List[str] = field(default_factory=list)
    images:          List[str] = field(default_factory=list)
    is_available:    bool      = True

    def __post_init__(self):
        if self.price_per_night: self._validate_price(self.price_per_night)
        if self.capacity:        self._validate_capacity(self.capacity)

    # ── Validations ────

    @staticmethod
    def _validate_price(price: float):
        if price <= 0:
            raise DomainValidationError("price_per_night", "Le prix doit être strictement positif.")

    @staticmethod
    def _validate_capacity(capacity: int):
        if not (1 <= capacity <= 20):
            raise DomainValidationError("capacity", "La capacité doit être entre 1 et 20 personnes.")

    # ── Comportements ───

    def activate(self):
        self.is_available = True
        self.touch()

    def deactivate(self):
        self.is_available = False
        self.touch()

    def compute_total_price(self, nights: int) -> float:
        """Prix total pour N nuits, arrondi à 2 décimales."""
        if nights <= 0:
            raise DomainValidationError("nights", "Le nombre de nuits doit être positif.")
        return round(self.price_per_night * nights, 2)

    def can_accommodate(self, guest_count: int) -> bool:
        return self.capacity >= guest_count

    def __str__(self) -> str:
        return f"{self.name} ({self.type.value}) — {self.price_per_night} {self.currency}/nuit"
