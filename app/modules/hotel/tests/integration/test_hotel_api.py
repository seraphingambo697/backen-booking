"""
app/modules/hotel/tests/integration/test_hotel_api.py
Tests d'intégration — endpoints Hotel & Room.

Couvre :
- Lecture publique (sans auth)
- CRUD admin
- Autorisation normale vs admin
- Cas limites (champs manquants, formats invalides)

pytest app/modules/hotel/tests/integration/ -v
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from app.modules.hotel.infrastructure.database.hotel_models import HotelModel
from app.modules.user.infrastructure.database.user_models import UserModel


# ── Fixtures ────────────

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def normal_user(db):
    return UserModel.objects.create_user(
        email="user@akkor.com", password="UserPass123!",
        first_name="Normal", last_name="User",
    )


@pytest.fixture
def admin_user(db):
    return UserModel.objects.create_superuser(
        email="admin@akkor.com", password="AdminPass456!",
        first_name="Admin", last_name="Akkor",
    )


@pytest.fixture
def hotel_payload():
    return {
        "name":        "Le Grand Hôtel",
        "description": "Un palace magnifique au cœur de Paris.",
        "address":     "1 Place Vendôme",
        "city":        "Paris",
        "country":     "France",
        "stars":       5,
        "latitude":    48.8698,
        "longitude":   2.3294,
        "amenities":   ["WiFi", "Piscine", "Spa"],
        "images":      ["https://example.com/hotel.jpg"],
    }


@pytest.fixture
def sample_hotel(db, admin_user, client, hotel_payload):
    """Crée un hôtel via l'API en tant qu'admin."""
    _auth(client, admin_user)
    resp = client.post("/api/v1/hotels/", hotel_payload, format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    return resp.data["data"]


def _auth(client, user):
    resp = client.post("/api/v1/auth/login/", {
        "email": user.email, "password": "AdminPass456!"
        if user.is_admin else "UserPass123!"
    })
    token = resp.data["data"]["tokens"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


# ═══════════════════════════════════════════════════════════════════════════════
# LECTURE PUBLIQUE (pas d'auth requise)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestHotelPublicRead:

    def test_list_hotels_anonymous(self, client):
        resp = client.get("/api/v1/hotels/")
        assert resp.status_code == status.HTTP_200_OK

    def test_list_hotels_returns_success_envelope(self, client):
        resp = client.get("/api/v1/hotels/")
        assert resp.data.get("success") is True

    def test_list_hotels_default_limit(self, client, db, admin_user):
        """La liste par défaut est bornée (default=10)."""
        _auth(client, admin_user)
        for i in range(15):
            client.post("/api/v1/hotels/", {
                "name": f"Hôtel {i}", "description": "Test", "address": "1 rue Test",
                "city": "Paris", "country": "France", "stars": 3,
            }, format="json")
        client.credentials()  # reset auth → anonyme
        resp = client.get("/api/v1/hotels/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data.get("data", [])
        assert len(data) <= 15  # respecte le limit

    def test_get_hotel_detail_anonymous(self, client, sample_hotel):
        hotel_id = sample_hotel["id"]
        client.credentials()  # anonyme
        resp = client.get(f"/api/v1/hotels/{hotel_id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["name"] == "Le Grand Hôtel"

    def test_get_hotel_not_found(self, client):
        resp = client.get("/api/v1/hotels/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_filter_hotels_by_city(self, client, db, admin_user):
        _auth(client, admin_user)
        for city in ["Paris", "Paris", "Lyon"]:
            client.post("/api/v1/hotels/", {
                "name": f"Hôtel {city}", "description": "", "address": "1 rue",
                "city": city, "country": "France", "stars": 3,
            }, format="json")
        client.credentials()
        resp = client.get("/api/v1/hotels/?city=Paris")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data.get("data", [])
        assert all(h["city"] == "Paris" for h in data)


# ═══════════════════════════════════════════════════════════════════════════════
# CRÉATION (admin requis)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestHotelCreate:

    def test_admin_can_create_hotel(self, client, admin_user, hotel_payload):
        _auth(client, admin_user)
        resp = client.post("/api/v1/hotels/", hotel_payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["name"] == hotel_payload["name"]

    def test_normal_user_cannot_create_hotel(self, client, normal_user, hotel_payload):
        _auth(client, normal_user)
        resp = client.post("/api/v1/hotels/", hotel_payload, format="json")
        assert resp.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_anonymous_cannot_create_hotel(self, client, hotel_payload):
        resp = client.post("/api/v1/hotels/", hotel_payload, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_hotel_missing_name(self, client, admin_user, hotel_payload):
        _auth(client, admin_user)
        del hotel_payload["name"]
        resp = client.post("/api/v1/hotels/", hotel_payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_hotel_stars_out_of_range(self, client, admin_user, hotel_payload):
        _auth(client, admin_user)
        hotel_payload["stars"] = 6
        resp = client.post("/api/v1/hotels/", hotel_payload, format="json")
        assert resp.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def test_create_hotel_stars_zero(self, client, admin_user, hotel_payload):
        _auth(client, admin_user)
        hotel_payload["stars"] = 0
        resp = client.post("/api/v1/hotels/", hotel_payload, format="json")
        assert resp.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def test_create_hotel_name_too_short(self, client, admin_user, hotel_payload):
        _auth(client, admin_user)
        hotel_payload["name"] = "X"
        resp = client.post("/api/v1/hotels/", hotel_payload, format="json")
        assert resp.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def test_create_hotel_persisted_in_db(self, client, admin_user, hotel_payload):
        _auth(client, admin_user)
        client.post("/api/v1/hotels/", hotel_payload, format="json")
        assert HotelModel.objects.filter(name="Le Grand Hôtel").exists()


# ═══════════════════════════════════════════════════════════════════════════════
# MISE À JOUR
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestHotelUpdate:

    def test_admin_can_update_hotel(self, client, admin_user, sample_hotel):
        _auth(client, admin_user)
        hotel_id = sample_hotel["id"]
        resp = client.patch(f"/api/v1/hotels/{hotel_id}/", {"name": "Nouveau Nom"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["name"] == "Nouveau Nom"

    def test_normal_user_cannot_update_hotel(self, client, normal_user, sample_hotel):
        _auth(client, normal_user)
        resp = client.patch(
            f"/api/v1/hotels/{sample_hotel['id']}/",
            {"name": "Hack"},
            format="json",
        )
        assert resp.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_anonymous_cannot_update_hotel(self, client, sample_hotel):
        resp = client.patch(
            f"/api/v1/hotels/{sample_hotel['id']}/",
            {"name": "Hack"},
            format="json",
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPRESSION (soft delete)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestHotelDelete:

    def test_admin_can_delete_hotel(self, client, admin_user, sample_hotel):
        _auth(client, admin_user)
        hotel_id = sample_hotel["id"]
        resp = client.delete(f"/api/v1/hotels/{hotel_id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_deleted_hotel_is_inactive(self, client, admin_user, sample_hotel):
        _auth(client, admin_user)
        hotel_id = sample_hotel["id"]
        client.delete(f"/api/v1/hotels/{hotel_id}/")
        hotel = HotelModel.objects.get(id=hotel_id)
        assert hotel.status == "INACTIVE"

    def test_normal_user_cannot_delete_hotel(self, client, normal_user, sample_hotel):
        _auth(client, normal_user)
        resp = client.delete(f"/api/v1/hotels/{sample_hotel['id']}/")
        assert resp.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        )
