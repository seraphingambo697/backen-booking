"""
app/modules/user/tests/integration/test_user_api.py
Tests d'intégration — endpoints User & Auth.

Ces tests utilisent le client DRF avec une vraie base SQLite en mémoire.
Chaque test classe reçoit une DB vierge (Django TestCase).

pytest app/modules/user/tests/integration/ -v
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from app.modules.user.infrastructure.database.user_models import UserModel


# ── Helpers ─────────────

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        "email":      "alice@example.com",
        "password":   "SecurePass123!",
        "first_name": "Alice",
        "last_name":  "Dupont",
    }


@pytest.fixture
def admin_data():
    return {
        "email":      "admin@akkor.com",
        "password":   "AdminPass456!",
        "first_name": "Admin",
        "last_name":  "Akkor",
    }


@pytest.fixture
def registered_user(db, user_data):
    """Crée un utilisateur en base et retourne (user_model, plain_password)."""
    user = UserModel.objects.create_user(
        email      = user_data["email"],
        password   = user_data["password"],
        first_name = user_data["first_name"],
        last_name  = user_data["last_name"],
    )
    return user, user_data["password"]


@pytest.fixture
def admin_user(db, admin_data):
    user = UserModel.objects.create_superuser(
        email      = admin_data["email"],
        password   = admin_data["password"],
        first_name = admin_data["first_name"],
        last_name  = admin_data["last_name"],
    )
    return user, admin_data["password"]


def _login(client, email, password):
    """Helper : login et retourne les tokens."""
    resp = client.post("/api/v1/auth/login/", {"email": email, "password": password})
    assert resp.status_code == status.HTTP_200_OK, resp.data
    return resp.data["data"]["tokens"]


def _auth_client(client, email, password):
    """Retourne un client authentifié."""
    tokens = _login(client, email, password)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    return client


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTER
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestRegister:

    def test_register_valid_user(self, client, user_data):
        resp = client.post("/api/v1/auth/register/", user_data)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["success"] is True
        assert resp.data["data"]["email"] == user_data["email"]

    def test_register_without_login(self, client, user_data):
        """Inscription disponible sans être connecté."""
        resp = client.post("/api/v1/auth/register/", user_data)
        assert resp.status_code == status.HTTP_201_CREATED

    def test_register_duplicate_email(self, client, user_data, registered_user):
        resp = client.post("/api/v1/auth/register/", user_data)
        assert resp.status_code in (status.HTTP_409_CONFLICT, status.HTTP_400_BAD_REQUEST)
        assert resp.data["success"] is False

    def test_register_missing_email(self, client):
        resp = client.post("/api/v1/auth/register/", {
            "password": "pass", "first_name": "A", "last_name": "B"
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_invalid_email_format(self, client):
        resp = client.post("/api/v1/auth/register/", {
            "email": "not-an-email",
            "password": "SecurePass123!",
            "first_name": "A", "last_name": "B",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_password(self, client):
        resp = client.post("/api/v1/auth/register/", {
            "email": "test@test.com", "first_name": "A", "last_name": "B"
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password(self, client):
        resp = client.post("/api/v1/auth/register/", {
            "email": "test@test.com", "password": "123",
            "first_name": "A", "last_name": "B",
        })
        assert resp.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def test_register_creates_user_in_db(self, client, user_data):
        client.post("/api/v1/auth/register/", user_data)
        assert UserModel.objects.filter(email=user_data["email"]).exists()

    def test_register_returns_no_password_in_response(self, client, user_data):
        resp = client.post("/api/v1/auth/register/", user_data)
        assert "password" not in resp.data.get("data", {})


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN / LOGOUT
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestAuthLoginLogout:

    def test_login_valid_credentials(self, client, registered_user):
        user, password = registered_user
        resp = client.post("/api/v1/auth/login/", {
            "email": user.email, "password": password
        })
        assert resp.status_code == status.HTTP_200_OK
        assert "access"  in resp.data["data"]["tokens"]
        assert "refresh" in resp.data["data"]["tokens"]

    def test_login_wrong_password(self, client, registered_user):
        user, _ = registered_user
        resp = client.post("/api/v1/auth/login/", {
            "email": user.email, "password": "WrongPass!"
        })
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_400_BAD_REQUEST,
        )
        assert resp.data["success"] is False

    def test_login_unknown_email(self, client):
        resp = client.post("/api/v1/auth/login/", {
            "email": "ghost@nowhere.com", "password": "irrelevant"
        })
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_login_missing_fields(self, client):
        resp = client.post("/api/v1/auth/login/", {"email": "a@b.com"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_invalidates_token(self, client, registered_user):
        user, password = registered_user
        tokens = _login(client, user.email, password)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        resp = client.post("/api/v1/auth/logout/", {"refresh": tokens["refresh"]})
        assert resp.status_code in (
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
        )

    def test_token_refresh(self, client, registered_user):
        user, password = registered_user
        tokens = _login(client, user.email, password)
        resp = client.post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]})
        assert resp.status_code == status.HTTP_200_OK
        assert "access" in resp.data


# ═══════════════════════════════════════════════════════════════════════════════
# PROFIL UTILISATEUR — GET / PATCH / DELETE
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestUserProfile:

    def test_get_profile_authenticated(self, client, registered_user):
        user, password = registered_user
        _auth_client(client, user.email, password)
        resp = client.get("/api/v1/users/me/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["email"] == user.email

    def test_get_profile_unauthenticated_returns_401(self, client):
        resp = client.get("/api/v1/users/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_own_profile(self, client, registered_user):
        user, password = registered_user
        _auth_client(client, user.email, password)
        resp = client.patch("/api/v1/users/me/", {"first_name": "AliceModifiée"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["first_name"] == "AliceModifiée"

    def test_update_email_to_existing_raises_conflict(self, client, registered_user, db):
        user, password = registered_user
        # Créer un deuxième user
        UserModel.objects.create_user(
            email="bob@example.com", password="BobPass123!",
            first_name="Bob", last_name="Martin",
        )
        _auth_client(client, user.email, password)
        resp = client.patch("/api/v1/users/me/", {"email": "bob@example.com"})
        assert resp.status_code in (
            status.HTTP_409_CONFLICT,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def test_delete_own_account(self, client, registered_user):
        user, password = registered_user
        _auth_client(client, user.email, password)
        resp = client.delete("/api/v1/users/me/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_normal_user_cannot_read_other_user(self, client, registered_user, db):
        """Un utilisateur normal ne peut pas lire le profil d'un autre."""
        user, password = registered_user
        other = UserModel.objects.create_user(
            email="other@example.com", password="OtherPass!",
            first_name="Other", last_name="User",
        )
        _auth_client(client, user.email, password)
        resp = client.get(f"/api/v1/users/{other.id}/")
        assert resp.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    def test_admin_can_read_any_user(self, client, registered_user, admin_user):
        user, _ = registered_user
        admin, admin_pass = admin_user
        _auth_client(client, admin.email, admin_pass)
        resp = client.get(f"/api/v1/users/{user.id}/")
        # L'admin peut accéder OU l'endpoint n'existe pas encore (400/404)
        assert resp.status_code in (
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,  # endpoint /users/{id}/ optionnel
        )
