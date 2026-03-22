"""
app/modules/booking/tests/integration/test_booking_api.py
Tests d'intégration — endpoints Booking.

Couvre :
- Création (auth requise)
- Lecture (user voit seulement ses bookings)
- Annulation avec résultat remboursement
- Disponibilité (public)
- Conflits de dates
- Cas limites

pytest app/modules/booking/tests/integration/ -v
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from app.modules.booking.infrastructure.database.booking_models import BookingModel
from app.modules.hotel.infrastructure.database.hotel_models import HotelModel, RoomModel
from app.modules.user.infrastructure.database.user_models import UserModel


# ── Helpers 

def _future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def alice(db):
    return UserModel.objects.create_user(
        email="alice@akkor.com", password="AlicePass123!",
        first_name="Alice", last_name="Martin",
    )


@pytest.fixture
def bob(db):
    return UserModel.objects.create_user(
        email="bob@akkor.com", password="BobPass456!",
        first_name="Bob", last_name="Dupont",
    )


@pytest.fixture
def admin(db):
    return UserModel.objects.create_superuser(
        email="admin@akkor.com", password="AdminPass789!",
        first_name="Admin", last_name="Akkor",
    )


@pytest.fixture
def hotel_and_room(db, admin):
    hotel = HotelModel.objects.create(
        owner_id=admin.id,
        name="Test Palace", description="Un bel hôtel",
        address="1 rue Test", city="Paris", country="France",
        stars=4, status="ACTIVE",
    )
    room = RoomModel.objects.create(
        hotel=hotel,
        name="Double Luxe", type="DOUBLE",
        description="Grande chambre", price_per_night=200.00,
        currency="EUR", capacity=2, size_sqm=30,
        is_available=True,
    )
    return hotel, room


def _login(client, user, password):
    resp = client.post("/api/v1/auth/login/", {"email": user.email, "password": password})
    assert resp.status_code == 200, resp.data
    token = resp.data["data"]["tokens"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def _booking_payload(hotel_and_room, check_in_days=3, check_out_days=6, adults=2):
    hotel, room = hotel_and_room
    return {
        "hotel_id":  str(hotel.id),
        "room_id":   str(room.id),
        "check_in":  _future(check_in_days),
        "check_out": _future(check_out_days),
        "guest_count": 2,
        "adults":    adults,
        "children":  0,
    }


# DISPONIBILITÉ

@pytest.mark.django_db
class TestAvailability:

    def test_availability_anonymous(self, client, hotel_and_room):
        """Test disponibilité d'un hôtel entre deux dates"""

        hotel, _ = hotel_and_room
        resp = client.post("/api/v1/bookings/availability/", {
            "hotel_id":  str(hotel.id),
            "check_in":  _future(5),
            "check_out": _future(8),
            "adults":    2,
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK

    def test_availability_returns_rooms_with_total_price(self, client, hotel_and_room):
        hotel, room = hotel_and_room
        resp = client.post("/api/v1/bookings/availability/", {
            "hotel_id":  str(hotel.id),
            "check_in":  _future(5),
            "check_out": _future(8),
            "adults":    2,
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data.get("data", [])
        assert len(data) == 1
        assert data[0]["nights"] == 3
        assert data[0]["total_price"] == 600.0  

    def test_availability_past_dates_rejected(self, client, hotel_and_room):
        hotel, _ = hotel_and_room
        resp = client.post("/api/v1/bookings/availability/", {
            "hotel_id":  str(hotel.id),
            "check_in":  "2020-01-01",
            "check_out": "2020-01-05",
            "adults":    2,
        }, format="json")
        assert resp.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

# CRÉATION DE RESERVATION

@pytest.mark.django_db
class TestBookingCreate:

    def test_authenticated_user_can_create_booking(self, client, alice, hotel_and_room):
        _login(client, alice, "AlicePass123!")
        resp = client.post("/api/v1/bookings/", _booking_payload(hotel_and_room), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["success"] is True

    def test_anonymous_cannot_create_booking(self, client, hotel_and_room):
        resp = client.post("/api/v1/bookings/", _booking_payload(hotel_and_room), format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_booking_price_calculated_correctly(self, client, alice, hotel_and_room):
        """3 nuits × 200€ = 600€"""
        _login(client, alice, "AlicePass123!")
        resp = client.post("/api/v1/bookings/", _booking_payload(
            hotel_and_room, check_in_days=5, check_out_days=8
        ), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["total_price"] == 600.0
        assert resp.data["data"]["nights"] == 3



# LECTURE

@pytest.mark.django_db
class TestBookingRead:

    def test_user_sees_only_own_bookings(self, client, alice, bob, hotel_and_room):
        
        # Alice réserve
        _login(client, alice, "AlicePass123!")
        client.post("/api/v1/bookings/", _booking_payload(
            hotel_and_room, check_in_days=2, check_out_days=5
        ), format="json")
        # Bob réserve des dates différentes
        _login(client, bob, "BobPass456!")
        client.post("/api/v1/bookings/", _booking_payload(
            hotel_and_room, check_in_days=10, check_out_days=13
        ), format="json")
        # Bob liste ses réservations
        resp = client.get("/api/v1/bookings/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data.get("data", [])
        for b in data:
            assert str(b["user_id"]) == str(bob.id)

    def test_get_booking_detail_own(self, client, alice, hotel_and_room):
        "detail de la reservation de l'utilisateur alice"
        _login(client, alice, "AlicePass123!")
        create_resp = client.post("/api/v1/bookings/", _booking_payload(hotel_and_room), format="json")
        booking_id = create_resp.data["data"]["id"]
        resp = client.get(f"/api/v1/bookings/{booking_id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == booking_id

   