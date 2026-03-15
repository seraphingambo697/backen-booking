"""
Tests unitaires Value Objects (DateRange, Money, GuestCount).
Ces objets sont partagés mais testés ici car surtout utilisés par booking.
pytest app/modules/booking/tests/unit/test_value_objects.py -v
"""
from datetime import date, timedelta

import pytest

from app.core.exceptions import DomainValidationError
from app.shared.domain.value_objects import DateRange, GuestCount, Money


# ── DateRange ───────────

class TestDateRange:

    def _range(self, delta_in=5, delta_out=8) -> DateRange:
        today = date.today()
        dr = object.__new__(DateRange)
        object.__setattr__(dr, "check_in",  today + timedelta(days=delta_in))
        object.__setattr__(dr, "check_out", today + timedelta(days=delta_out))
        return dr

    def test_nights(self):
        dr = self._range(5, 8)
        assert dr.nights == 3

    def test_overlaps_true(self):
        a = self._range(5, 10)
        b = self._range(8, 12)
        assert a.overlaps(b) is True

    def test_overlaps_false_adjacent(self):
        a = self._range(5, 8)
        b = self._range(8, 12)   # B commence quand A finit → pas chevauchement
        assert a.overlaps(b) is False

    def test_overlaps_false_separated(self):
        a = self._range(1, 3)
        b = self._range(5, 8)
        assert a.overlaps(b) is False

    def test_overlaps_contained(self):
        outer = self._range(1, 10)
        inner = self._range(3, 7)
        assert outer.overlaps(inner) is True

    def test_contains_date_inside(self):
        dr = self._range(5, 10)
        assert dr.contains(date.today() + timedelta(days=7)) is True

    def test_contains_date_at_checkout_is_false(self):
        dr = self._range(5, 10)
        # check_out lui-même n'est pas "dans" la plage [check_in, check_out[
        assert dr.contains(date.today() + timedelta(days=10)) is False

    def test_validate_max_nights_ok(self):
        dr = self._range(5, 10)  # 5 nuits
        dr.validate_max_nights(30)   # pas d'exception

    def test_validate_max_nights_exceeded(self):
        dr = self._range(5, 40)  # 35 nuits
        with pytest.raises(DomainValidationError) as exc:
            dr.validate_max_nights(30)
        assert exc.value.field == "check_out"

    def test_is_free_cancellation_far(self):
        dr = self._range(10, 14)
        assert dr.is_free_cancellation(min_hours=48) is True

    def test_is_not_free_cancellation_tomorrow(self):
        dr = self._range(1, 4)
        assert dr.is_free_cancellation(min_hours=48) is False

    def test_from_strings_valid(self):
        dr = DateRange.from_strings(
            str(date.today() + timedelta(days=5)),
            str(date.today() + timedelta(days=8)),
        )
        assert dr.nights == 3

    def test_from_strings_invalid_format(self):
        with pytest.raises(DomainValidationError):
            DateRange.from_strings("not-a-date", "2025-12-31")

    def test_checkout_before_checkin_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            DateRange(
                check_in  = date.today() + timedelta(days=8),
                check_out = date.today() + timedelta(days=5),
            )
        assert exc.value.field == "check_out"

    def test_checkin_in_past_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            DateRange(
                check_in  = date.today() - timedelta(days=1),
                check_out = date.today() + timedelta(days=3),
            )
        assert exc.value.field == "check_in"

    def test_str_representation(self):
        dr = self._range(5, 8)
        s = str(dr)
        assert "3 nuit" in s


# ── Money ───────────────

class TestMoney:

    def test_create(self):
        m = Money(150.0, "EUR")
        assert m.amount   == 150.0
        assert m.currency == "EUR"

    def test_negative_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            Money(-10.0, "EUR")
        assert exc.value.field == "amount"

    def test_invalid_currency_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            Money(10.0, "EU")   # doit être 3 lettres
        assert exc.value.field == "currency"

    def test_add(self):
        result = Money(100.0, "EUR").add(Money(50.0, "EUR"))
        assert result.amount == 150.0

    def test_add_different_currency_raises(self):
        with pytest.raises(DomainValidationError):
            Money(100.0, "EUR").add(Money(50.0, "USD"))

    def test_subtract(self):
        result = Money(100.0, "EUR").subtract(Money(30.0, "EUR"))
        assert result.amount == 70.0

    def test_subtract_below_zero_raises(self):
        with pytest.raises(DomainValidationError):
            Money(30.0, "EUR").subtract(Money(50.0, "EUR"))

    def test_multiply(self):
        result = Money(100.0, "EUR").multiply(3)
        assert result.amount == 300.0

    def test_apply_tax(self):
        result = Money(100.0, "EUR").apply_tax(0.10)
        assert result.amount == 110.0

    def test_apply_tax_invalid_rate(self):
        with pytest.raises(DomainValidationError):
            Money(100.0, "EUR").apply_tax(1.5)

    def test_zero(self):
        assert Money.zero().amount == 0.0

    def test_is_zero(self):
        assert Money.zero().is_zero() is True
        assert Money(1.0, "EUR").is_zero() is False

    def test_from_price_per_night(self):
        m = Money.from_price_per_night(150.0, nights=3, currency="EUR")
        assert m.amount   == 450.0
        assert m.currency == "EUR"

    def test_immutable(self):
        m = Money(100.0, "EUR")
        with pytest.raises(Exception):  # frozen dataclass
            m.amount = 200.0

    def test_is_greater_than(self):
        assert Money(200.0, "EUR").is_greater_than(Money(100.0, "EUR")) is True
        assert Money(50.0, "EUR").is_greater_than(Money(100.0, "EUR"))  is False


# ── GuestCount ──────────

class TestGuestCount:

    def test_total(self):
        g = GuestCount(adults=2, children=1)
        assert g.total == 3

    def test_no_adults_raises(self):
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

    def test_fits_in_capacity(self):
        g = GuestCount(adults=2, children=1)
        assert g.fits_in(3) is True
        assert g.fits_in(4) is True
        assert g.fits_in(2) is False

    def test_simple(self):
        g = GuestCount.simple(3)
        assert g.adults   == 3
        assert g.children == 0
        assert g.total    == 3

    def test_str_with_children(self):
        g = GuestCount(adults=2, children=1)
        assert "adulte" in str(g)
        assert "enfant" in str(g)

    def test_immutable(self):
        g = GuestCount(adults=2)
        with pytest.raises(Exception):
            g.adults = 5
