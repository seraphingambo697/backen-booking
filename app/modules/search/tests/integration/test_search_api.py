"""
app/modules/search/tests/integration/test_search_api.py
Tests d'intégration — endpoint de recherche.

pytest app/modules/search/tests/ -v
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from app.modules.hotel.infrastructure.database.hotel_models import HotelModel, RoomModel
from app.modules.user.infrastructure.database.user_models import UserModel


def _future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def setup_hotels(db):
    """Crée 2 hôtels Paris + 1 hôtel Lyon avec chambres."""
    admin = UserModel.objects.create_superuser(
        email="admin@search.test", password="Admin123!",
        first_name="Admin", last_name="Search",
    )
    h_paris1 = HotelModel.objects.create(
        owner_id=admin.id, name="Palace Paris", description="Top hôtel",
        address="1 rue Rivoli", city="Paris", country="France",
        stars=5, status="ACTIVE",
    )
    h_paris2 = HotelModel.objects.create(
        owner_id=admin.id, name="Budget Paris", description="Pas cher",
        address="10 rue du Faubourg", city="Paris", country="France",
        stars=3, status="ACTIVE",
    )
    h_lyon = HotelModel.objects.create(
        owner_id=admin.id, name="Hôtel Lyon", description="Centre-ville",
        address="1 place Bellecour", city="Lyon", country="France",
        stars=4, status="ACTIVE",
    )
    for hotel, price in [(h_paris1, 300.0), (h_paris2, 80.0), (h_lyon, 150.0)]:
        RoomModel.objects.create(
            hotel=hotel, name="Double", type="DOUBLE",
            description="Chambre double", price_per_night=price,
            currency="EUR", capacity=2, size_sqm=25, is_available=True,
        )
    return h_paris1, h_paris2, h_lyon


# ── Tests ────────────────

@pytest.mark.django_db
class TestSearchHotels:

    def _search(self, client, city="Paris", check_in_days=5, check_out_days=8,
                guest_count=2, **kwargs):
        payload = {
            "city":        city,
            "check_in":    _future(check_in_days),
            "check_out":   _future(check_out_days),
            "guest_count": guest_count,
            **kwargs,
        }
        return client.post("/api/v1/search/", payload, format="json")

    def test_search_returns_hotels_in_city(self, client, setup_hotels):
        resp = self._search(client, city="Paris")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data.get("data", resp.data.get("results", []))
        assert len(data) == 2  # 2 hôtels a paris


    def test_search_filters_by_stars(self, client, setup_hotels):
        resp = self._search(client, city="Paris", stars_min=5)
        data = resp.data.get("data", resp.data.get("results", []))
        for r in data:
            assert r["hotel"]["stars"] >= 5

    def test_search_filters_by_price_max(self, client, setup_hotels):
        resp = self._search(client, city="Paris", price_max=100.0)
        data = resp.data.get("data", resp.data.get("results", []))
        for r in data:
            assert r["min_price"] <= 100.0

    def test_search_empty_city_returns_no_results(self, client, setup_hotels):
        resp = self._search(client, city="VilleInexistante")
        data = resp.data.get("data", resp.data.get("results", []))
        assert len(data) == 0

    def test_search_invalid_dates_rejected(self, client, setup_hotels):
        resp = client.post("/api/v1/search/", {
            "city": "Paris",
            "check_in":  _future(10),
            "check_out": _future(5),  # avant check_in
            "guest_count": 2,
        }, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_returns_nights_count(self, client, setup_hotels):
        resp = self._search(client, check_in_days=5, check_out_days=8)  # 3 nuits
        data = resp.data.get("data", resp.data.get("results", []))
        if data:
            assert data[0].get("nights") == 3
