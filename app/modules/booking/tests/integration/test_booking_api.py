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


# ── Helpers ─────────────

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
        "adults":    adults,
        "children":  0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DISPONIBILITÉ (public)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestAvailability:

    def test_availability_anonymous(self, client, hotel_and_room):
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
        assert data[0]["total_price"] == 600.0  # 200 × 3 nuits

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

    def test_availability_check_out_before_check_in(self, client, hotel_and_room):
        hotel, _ = hotel_and_room
        resp = client.post("/api/v1/bookings/availability/", {
            "hotel_id":  str(hotel.id),
            "check_in":  _future(10),
            "check_out": _future(5),
            "adults":    2,
        }, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ═══════════════════════════════════════════════════════════════════════════════
# CRÉATION
# ═══════════════════════════════════════════════════════════════════════════════

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

    def test_booking_status_is_pending(self, client, alice, hotel_and_room):
        _login(client, alice, "AlicePass123!")
        resp = client.post("/api/v1/bookings/", _booking_payload(hotel_and_room), format="json")
        assert resp.data["data"]["status"] == "PENDING"

    def test_booking_date_conflict_raises_409(self, client, alice, bob, hotel_and_room):
        """Deux réservations sur les mêmes dates → conflit."""
        payload = _booking_payload(hotel_and_room, check_in_days=10, check_out_days=14)
        # Alice réserve
        _login(client, alice, "AlicePass123!")
        resp1 = client.post("/api/v1/bookings/", payload, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED
        # Bob essaie les mêmes dates
        _login(client, bob, "BobPass456!")
        resp2 = client.post("/api/v1/bookings/", payload, format="json")
        assert resp2.status_code == status.HTTP_409_CONFLICT
        assert resp2.data["error"]["code"] == "booking_conflict"

    def test_booking_past_dates_rejected(self, client, alice, hotel_and_room):
        hotel, room = hotel_and_room
        _login(client, alice, "AlicePass123!")
        resp = client.post("/api/v1/bookings/", {
            "hotel_id":  str(hotel.id),
            "room_id":   str(room.id),
            "check_in":  "2020-01-01",
            "check_out": "2020-01-05",
            "adults": 2,
        }, format="json")
        assert resp.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def test_booking_room_not_found(self, client, alice, hotel_and_room):
        hotel, _ = hotel_and_room
        _login(client, alice, "AlicePass123!")
        resp = client.post("/api/v1/bookings/", {
            "hotel_id":  str(hotel.id),
            "room_id":   "00000000-0000-0000-0000-000000000000",
            "check_in":  _future(3),
            "check_out": _future(6),
            "adults": 2,
        }, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_booking_persisted_in_db(self, client, alice, hotel_and_room):
        _login(client, alice, "AlicePass123!")
        client.post("/api/v1/bookings/", _booking_payload(hotel_and_room), format="json")
        assert BookingModel.objects.filter(user_id=alice.id).exists()


# ═══════════════════════════════════════════════════════════════════════════════
# LECTURE
# ═══════════════════════════════════════════════════════════════════════════════

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
        _login(client, alice, "AlicePass123!")
        create_resp = client.post("/api/v1/bookings/", _booking_payload(hotel_and_room), format="json")
        booking_id = create_resp.data["data"]["id"]
        resp = client.get(f"/api/v1/bookings/{booking_id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == booking_id

    def test_get_booking_detail_other_user_forbidden(self, client, alice, bob, hotel_and_room):
        _login(client, alice, "AlicePass123!")
        create_resp = client.post("/api/v1/bookings/", _booking_payload(hotel_and_room), format="json")
        booking_id = create_resp.data["data"]["id"]
        _login(client, bob, "BobPass456!")
        resp = client.get(f"/api/v1/bookings/{booking_id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_read_any_booking(self, client, alice, admin, hotel_and_room):
        _login(client, alice, "AlicePass123!")
        create_resp = client.post("/api/v1/bookings/", _booking_payload(hotel_and_room), format="json")
        booking_id = create_resp.data["data"]["id"]
        _login(client, admin, "AdminPass789!")
        resp = client.get(f"/api/v1/bookings/{booking_id}/")
        assert resp.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_list_bookings(self, client):
        resp = client.get("/api/v1/bookings/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_booking_not_found(self, client, alice):
        _login(client, alice, "AlicePass123!")
        resp = client.get("/api/v1/bookings/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_filter_bookings_by_status(self, client, alice, hotel_and_room):
        _login(client, alice, "AlicePass123!")
        client.post("/api/v1/bookings/", _booking_payload(hotel_and_room), format="json")
        resp = client.get("/api/v1/bookings/?status=PENDING")
        assert resp.status_code == status.HTTP_200_OK
        for b in resp.data.get("data", []):
            assert b["status"] == "PENDING"


# ═══════════════════════════════════════════════════════════════════════════════
# ANNULATION
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestBookingCancel:

    def _create_booking(self, client, user, password, hotel_and_room, **kw):
        _login(client, user, password)
        resp = client.post("/api/v1/bookings/", _booking_payload(hotel_and_room, **kw), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        return resp.data["data"]["id"]

    def test_owner_can_cancel_booking(self, client, alice, hotel_and_room):
        booking_id = self._create_booking(client, alice, "AlicePass123!", hotel_and_room)
        resp = client.delete(f"/api/v1/bookings/{booking_id}/", {"reason": "Changement de plan"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["booking"]["status"] == "CANCELLED"

    def test_cancel_response_has_refund_info(self, client, alice, hotel_and_room):
        booking_id = self._create_booking(
            client, alice, "AlicePass123!", hotel_and_room,
            check_in_days=60, check_out_days=63
        )
        resp = client.delete(f"/api/v1/bookings/{booking_id}/", {"reason": ""}, format="json")
        assert "is_free"         in resp.data["data"]
        assert "refund_amount"   in resp.data["data"]
        assert "refund_currency" in resp.data["data"]

    def test_free_cancellation_far_future(self, client, alice, hotel_and_room):
        """Check_in dans 60 jours → annulation gratuite."""
        booking_id = self._create_booking(
            client, alice, "AlicePass123!", hotel_and_room,
            check_in_days=60, check_out_days=63,
        )
        resp = client.delete(f"/api/v1/bookings/{booking_id}/", {}, format="json")
        assert resp.data["data"]["is_free"] is True
        assert resp.data["data"]["refund_amount"] == 600.0  # 200 × 3 nuits

    def test_other_user_cannot_cancel(self, client, alice, bob, hotel_and_room):
        booking_id = self._create_booking(client, alice, "AlicePass123!", hotel_and_room)
        _login(client, bob, "BobPass456!")
        resp = client.delete(f"/api/v1/bookings/{booking_id}/", {}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_cancel_nonexistent_booking(self, client, alice):
        _login(client, alice, "AlicePass123!")
        resp = client.delete("/api/v1/bookings/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_can_cancel_any_booking(self, client, alice, admin, hotel_and_room):
        booking_id = self._create_booking(client, alice, "AlicePass123!", hotel_and_room)
        _login(client, admin, "AdminPass789!")
        resp = client.delete(f"/api/v1/bookings/{booking_id}/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
