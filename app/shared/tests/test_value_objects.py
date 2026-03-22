"""
Tests unitaires des Value Objects .
pytest app/shared/tests/test_value_objects.py -v
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.core.exceptions import DomainValidationError
from app.shared.domain.value_objects import DateRange, GuestCount, Money


# DateRange

class TestDateRange:

    def _future(self, days=1) -> date:
        """Retourne une date dans le futur."""
        return date.today() + timedelta(days=days)
    def test_valid_range(self):
        """Test une plage de dates valide."""
        dr = DateRange(self._future(1), self._future(4))
        assert dr.nights == 3

    def test_check_out_before_check_in_raises(self):
        """Test une plage de dates invalide : check_out avant check_in."""
        with pytest.raises(DomainValidationError) as exc:
            DateRange(self._future(5), self._future(2))
        assert exc.value.field == "check_out"

    def test_same_day_raises(self):
        """Test une plage de dates invalide : check_in et check_out égaux."""
        d = self._future(2)
        with pytest.raises(DomainValidationError):
            DateRange(d, d)

    def test_past_check_in_raises(self):
        """Test une plage de dates invalide : check_in dans le passé."""
        with pytest.raises(DomainValidationError) as exc:
            DateRange(date.today() - timedelta(days=1), self._future(2))
        assert exc.value.field == "check_in"

    def test_today_check_in_is_valid(self):
        """Test une plage de dates valide : check_in aujourd'hui."""
        dr = DateRange(date.today(), self._future(2))
        assert dr.nights == 2

    def test_nights_calculation(self):
        """Test le calcul du nombre de nuits."""
        dr = DateRange(self._future(1), self._future(8))
        assert dr.nights == 7


    def test_contains_date(self):
        """Test si une date est dans la plage de dates."""
        dr = DateRange(self._future(2), self._future(6))
        assert dr.contains(self._future(3)) is True
        assert dr.contains(self._future(6)) is False  
        assert dr.contains(self._future(2)) is True   

    def test_validate_max_nights_ok(self):
        """Test une plage de dates valide : durée inférieure au maximum qui est 30 jours."""
        dr = DateRange(self._future(1), self._future(5))
        dr.validate_max_nights(30)  

    def test_validate_max_nights_exceeded(self):
        """Test une plage de dates invalide : durée supérieure au maximum qui est 30 jours."""
        dr = DateRange(self._future(1), self._future(35))
        with pytest.raises(DomainValidationError) as exc:
            dr.validate_max_nights(30)
        assert exc.value.field == "check_out"


# montant de la réservation

class TestMoney:

    def test_create_valid(self):
        """Test un montant valide."""
        m = Money(150.0, "EUR")
        assert m.amount == 150.0
        assert m.currency == "EUR"

    def test_negative_amount_raises(self):
        """Test un montant négatif."""
        with pytest.raises(DomainValidationError) as exc:
            Money(-1.0, "EUR")
        assert exc.value.field == "amount"

    def test_invalid_currency_raises(self):
        """Test une devise invalide."""
        with pytest.raises(DomainValidationError) as exc:
            Money(100.0, "EURO")
        assert exc.value.field == "currency"

    def test_empty_currency_raises(self):
        """Test une devise vide."""
        with pytest.raises(DomainValidationError):
            Money(100.0, "")

    def test_add(self):
        """Test l'addition de deux montants."""
        result = Money(100.0, "EUR").add(Money(50.0, "EUR"))
        assert result.amount == 150.0

    def test_add_different_currencies_raises(self):
        """Test une addition de montants avec des devises différentes."""
        with pytest.raises(DomainValidationError):
            Money(100.0, "EUR").add(Money(50.0, "USD"))

    def test_subtract(self):
        """Test la soustraction de deux montants."""
        result = Money(150.0, "EUR").subtract(Money(50.0, "EUR"))
        assert result.amount == 100.0

    def test_subtract_negative_result_raises(self):
        """Test une soustraction de montants avec un résultat négatif."""
        with pytest.raises(DomainValidationError):
            Money(50.0, "EUR").subtract(Money(100.0, "EUR"))

    def test_multiply(self):
        """Test la multiplication d'un montant par un facteur."""
        result = Money(100.0, "EUR").multiply(3)
        assert result.amount == 300.0



    def test_apply_tax(self):
        """Test l'application d'une taxe sur un montant."""
        result = Money(100.0, "EUR").apply_tax(0.20)
        assert result.amount == 120.0

    def test_apply_tax_invalid_rate(self):
        """Test une taxe invalide. car le taux de taxe doit être compris entre 0 et 1."""
        with pytest.raises(DomainValidationError):
            Money(100.0, "EUR").apply_tax(1.5)


    def test_from_price_per_night(self):
        """Test la création d'un montant à partir du prix par nuit et du nombre de nuits."""
        m = Money.from_price_per_night(150.0, 3, "EUR")
        assert m.amount == 450.0


# ═══════════════════════════════════════════════════════════════════════════════
# GuestCount(tester le nombre de personne adultes et enfants)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGuestCount:

    def test_valid_adults_only(self):
        """Test un nombre valide d'adultes."""
        g = GuestCount(adults=2)
        assert g.total == 2
        assert g.children == 0

    def test_valid_adults_and_children(self):
        """Test un nombre valide d'adultes et d'enfants."""
        g = GuestCount(adults=2, children=3)
        assert g.total == 5


    def test_negative_children_raises(self):
        """Test un nombre négatif d'enfants."""
        with pytest.raises(DomainValidationError) as exc:
            GuestCount(adults=1, children=-1)
        assert exc.value.field == "children"
