"""
Tests unitaires des Value Objects .
pytest app/shared/tests/test_value_objects.py -v
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.core.exceptions import DomainValidationError
from app.shared.domain.value_objects import DateRange, GuestCount, Money


# ═══════════════════════════════════════════════════════════════════════════════
# DateRange
# ═══════════════════════════════════════════════════════════════════════════════

class TestDateRange:

    def _future(self, days=1) -> date:
        """Retourne une date dans le futur."""
        return date.today() + timedelta(days=days)
    def test_valid_range(self):
        """Test une plage de dates valide."""
        dr = DateRange(self._future(1), self._future(4))
        assert dr.nights == 3

    def test_check_out_before_check_in_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            DateRange(self._future(5), self._future(2))
        assert exc.value.field == "check_out"

    def test_same_day_raises(self):
        d = self._future(2)
        with pytest.raises(DomainValidationError):
            DateRange(d, d)

    def test_past_check_in_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            DateRange(date.today() - timedelta(days=1), self._future(2))
        assert exc.value.field == "check_in"

    def test_today_check_in_is_valid(self):
        dr = DateRange(date.today(), self._future(2))
        assert dr.nights == 2

    def test_nights_calculation(self):
        dr = DateRange(self._future(1), self._future(8))
        assert dr.nights == 7

    def test_overlaps_true(self):
        dr1 = DateRange(self._future(1), self._future(5))
        dr2 = DateRange(self._future(3), self._future(8))
        assert dr1.overlaps(dr2) is True
        assert dr2.overlaps(dr1) is True

    def test_overlaps_false_adjacent(self):
        """Deux séjours adjacents ne se chevauchent pas."""
        dr1 = DateRange(self._future(1), self._future(4))
        dr2 = DateRange(self._future(4), self._future(7))
        assert dr1.overlaps(dr2) is False

    def test_overlaps_false_separate(self):
        dr1 = DateRange(self._future(1), self._future(3))
        dr2 = DateRange(self._future(5), self._future(8))
        assert dr1.overlaps(dr2) is False

    def test_contains_date(self):
        dr = DateRange(self._future(2), self._future(6))
        assert dr.contains(self._future(3)) is True
        assert dr.contains(self._future(6)) is False  # check_out exclu
        assert dr.contains(self._future(2)) is True   # check_in inclus

    def test_validate_max_nights_ok(self):
        dr = DateRange(self._future(1), self._future(5))
        dr.validate_max_nights(30)  # ne lève pas

    def test_validate_max_nights_exceeded(self):
        dr = DateRange(self._future(1), self._future(35))
        with pytest.raises(DomainValidationError) as exc:
            dr.validate_max_nights(30)
        assert exc.value.field == "check_out"

    def test_from_strings(self):
        ci = self._future(2).isoformat()
        co = self._future(5).isoformat()
        dr = DateRange.from_strings(ci, co)
        assert dr.nights == 3

    def test_from_strings_invalid_format(self):
        with pytest.raises(DomainValidationError):
            DateRange.from_strings("not-a-date", "2025-12-31")

    def test_str_representation(self):
        dr = DateRange(self._future(1), self._future(3))
        assert "→" in str(dr)
        assert "2 nuit" in str(dr)


# ═══════════════════════════════════════════════════════════════════════════════
# Money
# ═══════════════════════════════════════════════════════════════════════════════

class TestMoney:

    def test_create_valid(self):
        m = Money(150.0, "EUR")
        assert m.amount == 150.0
        assert m.currency == "EUR"

    def test_negative_amount_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            Money(-1.0, "EUR")
        assert exc.value.field == "amount"

    def test_invalid_currency_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            Money(100.0, "EURO")
        assert exc.value.field == "currency"

    def test_empty_currency_raises(self):
        with pytest.raises(DomainValidationError):
            Money(100.0, "")

    def test_add(self):
        result = Money(100.0, "EUR").add(Money(50.0, "EUR"))
        assert result.amount == 150.0

    def test_add_different_currencies_raises(self):
        with pytest.raises(DomainValidationError):
            Money(100.0, "EUR").add(Money(50.0, "USD"))

    def test_subtract(self):
        result = Money(150.0, "EUR").subtract(Money(50.0, "EUR"))
        assert result.amount == 100.0

    def test_subtract_negative_result_raises(self):
        with pytest.raises(DomainValidationError):
            Money(50.0, "EUR").subtract(Money(100.0, "EUR"))

    def test_multiply(self):
        result = Money(100.0, "EUR").multiply(3)
        assert result.amount == 300.0

    def test_multiply_float(self):
        result = Money(99.99, "EUR").multiply(3)
        assert result.amount == 299.97

    def test_apply_tax(self):
        result = Money(100.0, "EUR").apply_tax(0.20)
        assert result.amount == 120.0

    def test_apply_tax_invalid_rate(self):
        with pytest.raises(DomainValidationError):
            Money(100.0, "EUR").apply_tax(1.5)

    def test_zero_factory(self):
        m = Money.zero("USD")
        assert m.amount == 0.0
        assert m.is_zero() is True

    def test_from_price_per_night(self):
        m = Money.from_price_per_night(150.0, 3, "EUR")
        assert m.amount == 450.0

    def test_is_greater_than(self):
        assert Money(200.0, "EUR").is_greater_than(Money(100.0, "EUR")) is True
        assert Money(50.0,  "EUR").is_greater_than(Money(100.0, "EUR")) is False

    def test_immutability(self):
        m = Money(100.0, "EUR")
        result = m.add(Money(50.0, "EUR"))
        assert m.amount == 100.0  # original inchangé
        assert result.amount == 150.0

    def test_str_representation(self):
        assert str(Money(150.0, "EUR")) == "150.00 EUR"


# ═══════════════════════════════════════════════════════════════════════════════
# GuestCount
# ═══════════════════════════════════════════════════════════════════════════════

class TestGuestCount:

    def test_valid_adults_only(self):
        g = GuestCount(adults=2)
        assert g.total == 2
        assert g.children == 0

    def test_valid_adults_and_children(self):
        g = GuestCount(adults=2, children=3)
        assert g.total == 5

    def test_zero_adults_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            GuestCount(adults=0)
        assert exc.value.field == "adults"

    def test_negative_children_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            GuestCount(adults=1, children=-1)
        assert exc.value.field == "children"

    def test_too_many_guests_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            GuestCount(adults=15, children=10)
        assert exc.value.field == "guests"

    def test_fits_in_true(self):
        assert GuestCount(2, 1).fits_in(4) is True
        assert GuestCount(2, 1).fits_in(3) is True

    def test_fits_in_false(self):
        assert GuestCount(2, 2).fits_in(3) is False

    def test_simple_factory(self):
        g = GuestCount.simple(4)
        assert g.adults == 4
        assert g.children == 0
        assert g.total == 4

    def test_str_adults_only(self):
        assert "adulte" in str(GuestCount(2))

    def test_str_with_children(self):
        s = str(GuestCount(2, 1))
        assert "adulte" in s
        assert "enfant" in s
