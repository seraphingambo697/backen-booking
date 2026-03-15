"""
conftest.py — fixtures pytest partagées pour tout le projet.

Placé à la racine du projet, disponible dans tous les modules de test.
"""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from app.modules.hotel.infrastructure.database.hotel_models import HotelModel, RoomModel
from app.modules.user.infrastructure.database.user_models import UserModel


# ══════════════════════════════════════════════════════════════════════════════
# Clients HTTP
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def api_client():
    """Client DRF non authentifié."""
    return APIClient()


@pytest.fixture
def auth_client(api_client, normal_user):
    """Client DRF authentifié en tant qu'utilisateur normal."""
    resp = api_client.post("/api/v1/auth/login/", {
        "email": "user@conftest.com", "password": "TestPass123!"
    })
    token = resp.data["data"]["tokens"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Client DRF authentifié en tant qu'admin."""
    resp = api_client.post("/api/v1/auth/login/", {
        "email": "admin@conftest.com", "password": "AdminPass123!"
    })
    token = resp.data["data"]["tokens"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


# ══════════════════════════════════════════════════════════════════════════════
# Utilisateurs
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def normal_user(db):
    """Utilisateur normal en base."""
    return UserModel.objects.create_user(
        email      = "user@conftest.com",
        password   = "TestPass123!",
        first_name = "Test",
        last_name  = "User",
    )


@pytest.fixture
def admin_user(db):
    """Administrateur en base."""
    return UserModel.objects.create_superuser(
        email      = "admin@conftest.com",
        password   = "AdminPass123!",
        first_name = "Admin",
        last_name  = "Conftest",
    )


@pytest.fixture
def second_user(db):
    """Second utilisateur normal (pour tester l'isolation)."""
    return UserModel.objects.create_user(
        email      = "other@conftest.com",
        password   = "OtherPass123!",
        first_name = "Other",
        last_name  = "User",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Hôtels & Chambres
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_hotel(db, admin_user):
    """Hôtel de test actif."""
    return HotelModel.objects.create(
        owner_id   = admin_user.id,
        name       = "Conftest Palace",
        description= "Hôtel de test",
        address    = "1 rue Test",
        city       = "Paris",
        country    = "France",
        stars      = 4,
        status     = "ACTIVE",
        latitude   = 48.8698,
        longitude  = 2.3079,
    )


@pytest.fixture
def sample_room(db, sample_hotel):
    """Chambre double de test."""
    return RoomModel.objects.create(
        hotel          = sample_hotel,
        name           = "Double Conftest",
        type           = "DOUBLE",
        description    = "Chambre de test",
        price_per_night= 150.00,
        currency       = "EUR",
        capacity       = 2,
        size_sqm       = 25,
        is_available   = True,
    )


@pytest.fixture
def suite_room(db, sample_hotel):
    """Suite de luxe de test."""
    return RoomModel.objects.create(
        hotel          = sample_hotel,
        name           = "Suite Conftest",
        type           = "SUITE",
        description    = "Suite de test",
        price_per_night= 400.00,
        currency       = "EUR",
        capacity       = 4,
        size_sqm       = 80,
        is_available   = True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def future_dates():
    """Tuple (check_in, check_out) en chaînes ISO pour 3 nuits dans 10 jours."""
    from datetime import date, timedelta
    check_in  = date.today() + timedelta(days=10)
    check_out = date.today() + timedelta(days=13)
    return check_in.isoformat(), check_out.isoformat()


@pytest.fixture
def login_as(api_client):
    """Factory pour obtenir un client authentifié pour n'importe quel user."""
    def _login(user, password):
        resp = api_client.post("/api/v1/auth/login/", {
            "email": user.email, "password": password
        })
        assert resp.status_code == 200, f"Login failed: {resp.data}"
        token = resp.data["data"]["tokens"]["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return api_client
    return _login
