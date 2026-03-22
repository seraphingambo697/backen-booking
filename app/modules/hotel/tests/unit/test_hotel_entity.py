"""
Tests unitaires Hotel & Room — pur Python, pas de Django.
pytest app/modules/hotel/tests/unit/ -v
"""
import pytest
from app.core.exceptions import DomainValidationError
from app.modules.hotel.domain.entities.hotel import Hotel, HotelStatus, Room, RoomType


# ── Helpers ─────────────

def make_hotel(**kwargs) -> Hotel:
    defaults = dict(name="Le Meurice", description="Palace parisien",
                    address="228 Rue de Rivoli", city="Paris", country="France",
                    stars=5, owner_id="owner-123")
    defaults.update(kwargs)
    return Hotel(**defaults)


def make_room(**kwargs) -> Room:
    defaults = dict(hotel_id="hotel-123", name="Chambre Double", type=RoomType.DOUBLE,
                    price_per_night=250.0, capacity=2, size_sqm=30)
    defaults.update(kwargs)
    return Room(**defaults)


# ── Hotel ───────────────

class TestHotelEntity:

    def test_create_valid_hotel(self):
        h = make_hotel()
        assert h.name == "Le Meurice"
        assert h.status == HotelStatus.ACTIVE
        assert h.is_active is True

    def test_deactivate(self):
        h = make_hotel()
        h.deactivate()
        assert h.status == HotelStatus.INACTIVE
        assert h.is_active is False

    def test_activate(self):
        h = make_hotel()
        h.deactivate()
        h.activate()
        assert h.is_active is True

    def test_add_amenity(self):
        h = make_hotel()
        h.add_amenity("Piscine")
        assert "Piscine" in h.amenities

    def test_remove_amenity(self):
        h = make_hotel(amenities=["WiFi", "Spa"])
        h.remove_amenity("WiFi")
        assert "WiFi" not in h.amenities
        assert "Spa" in h.amenities

    def test_is_owned_by(self):
        h = make_hotel(owner_id="user-abc")
        assert h.is_owned_by("user-abc") is True
        assert h.is_owned_by("user-xyz") is False

