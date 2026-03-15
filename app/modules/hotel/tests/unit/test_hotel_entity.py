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

    def test_stars_too_high_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            make_hotel(stars=6)
        assert exc.value.field == "stars"

    def test_stars_zero_raises(self):
        with pytest.raises(DomainValidationError):
            make_hotel(stars=0)

    def test_name_too_short_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            make_hotel(name="X")
        assert exc.value.field == "name"

    def test_invalid_email_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            make_hotel(email="not-an-email")
        assert exc.value.field == "email"

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

    def test_add_amenity_no_duplicate(self):
        h = make_hotel(amenities=["Piscine"])
        h.add_amenity("Piscine")
        assert h.amenities.count("Piscine") == 1

    def test_remove_amenity(self):
        h = make_hotel(amenities=["WiFi", "Spa"])
        h.remove_amenity("WiFi")
        assert "WiFi" not in h.amenities
        assert "Spa" in h.amenities

    def test_average_rating_empty(self):
        h = make_hotel()
        assert h.compute_average_rating([]) == 0.0

    def test_average_rating(self):
        h = make_hotel()
        assert h.compute_average_rating([4.0, 5.0, 4.5]) == 4.5

    def test_is_owned_by(self):
        h = make_hotel(owner_id="user-abc")
        assert h.is_owned_by("user-abc") is True
        assert h.is_owned_by("user-xyz") is False


# ── Room ────────────────

class TestRoomEntity:

    def test_create_valid_room(self):
        r = make_room()
        assert r.type == RoomType.DOUBLE
        assert r.is_available is True
        assert r.currency == "EUR"

    def test_price_zero_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            make_room(price_per_night=0)
        assert exc.value.field == "price_per_night"

    def test_price_negative_raises(self):
        with pytest.raises(DomainValidationError):
            make_room(price_per_night=-50.0)

    def test_capacity_too_high_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            make_room(capacity=25)
        assert exc.value.field == "capacity"

    def test_deactivate_room(self):
        r = make_room()
        r.deactivate()
        assert r.is_available is False

    def test_activate_room(self):
        r = make_room()
        r.deactivate()
        r.activate()
        assert r.is_available is True

    def test_compute_total_price(self):
        r = make_room(price_per_night=150.0)
        assert r.compute_total_price(3) == 450.0

    def test_compute_total_price_rounding(self):
        r = make_room(price_per_night=99.99)
        assert r.compute_total_price(3) == 299.97

    def test_compute_total_price_zero_nights(self):
        r = make_room()
        with pytest.raises(DomainValidationError):
            r.compute_total_price(0)

    def test_can_accommodate(self):
        r = make_room(capacity=3)
        assert r.can_accommodate(2) is True
        assert r.can_accommodate(3) is True
        assert r.can_accommodate(4) is False

    def test_room_type_enum(self):
        for t in ["SINGLE","DOUBLE","TWIN","SUITE","DELUXE","FAMILY"]:
            r = make_room(type=RoomType(t))
            assert r.type.value == t
