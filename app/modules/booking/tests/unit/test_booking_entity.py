"""
Tests unitaires Booking entity — pur Python,
pytest app/modules/booking/tests/unit/ -v
"""
from datetime import date, datetime, timedelta

import pytest

from app.core.exceptions import BookingStateError
from app.modules.booking.domain.entities.booking import Booking, BookingStatus
from app.shared.domain.value_objects import DateRange, GuestCount, Money


# ── Helper factory

def make_booking(
    status: BookingStatus = BookingStatus.PENDING,
    days_until_checkin: int = 10,
    nights: int = 3,
    total: float = 450.0,
) -> Booking:
    today     = date.today()
    check_in  = today + timedelta(days=days_until_checkin)
    check_out = check_in + timedelta(days=nights)

    b = Booking.__new__(Booking)
    object.__setattr__(b, "id",                   "bid-001")
    object.__setattr__(b, "user_id",              "uid-001")
    object.__setattr__(b, "hotel_id",             "hid-001")
    object.__setattr__(b, "room_id",              "rid-001")
    object.__setattr__(b, "status",               status)
    object.__setattr__(b, "special_requests",     "")
    object.__setattr__(b, "cancelled_at",         None)
    object.__setattr__(b, "cancellation_reason",  "")
    object.__setattr__(b, "created_at",           datetime.utcnow())
    object.__setattr__(b, "updated_at",           datetime.utcnow())
    object.__setattr__(b, "_events",              [])

    dr = object.__new__(DateRange)
    object.__setattr__(dr, "check_in",  check_in)
    object.__setattr__(dr, "check_out", check_out)
    object.__setattr__(b, "date_range", dr)

    money = object.__new__(Money)
    object.__setattr__(money, "amount",   total)
    object.__setattr__(money, "currency", "EUR")
    object.__setattr__(b, "total", money)

    guests = object.__new__(GuestCount)
    object.__setattr__(guests, "adults",   2)
    object.__setattr__(guests, "children", 0)
    object.__setattr__(b, "guests", guests)

    return b


# ── Propriétés calculées 

class TestBookingProperties:

    def test_nights(self):
        b = make_booking(nights=4)
        assert b.nights == 4

    def test_guest_count(self):
        b = make_booking()
        assert b.guest_count == 2

    def test_total_price(self):
        b = make_booking(total=600.0)
        assert b.total_price == 600.0

    def test_currency(self):
        b = make_booking()
        assert b.currency == "EUR"

    def test_check_in_check_out(self):

        b = make_booking(days_until_checkin=5, nights=2)
        assert b.check_in  == date.today() + timedelta(days=5)
        assert b.check_out == date.today() + timedelta(days=7)


# ── Machine à états ─────

class TestBookingStateMachine:
    "Changement d'etat de notre booking"

    def test_pending_to_confirmed(self):
        "pending - confirmed"
        b = make_booking(status=BookingStatus.PENDING)
        b.confirm()
        assert b.status == BookingStatus.CONFIRMED

    def test_pending_to_cancelled(self):
        "pending - canceled"
        b = make_booking(status=BookingStatus.PENDING)
        b.cancel(reason="Plus besoin")
        assert b.status         == BookingStatus.CANCELLED
        assert b.cancellation_reason == "Plus besoin"
        assert b.cancelled_at is not None

    def test_confirmed_to_completed(self):
        "confirmer - complete"
        b = make_booking(status=BookingStatus.CONFIRMED)
        b.complete()
        assert b.status == BookingStatus.COMPLETED

    def test_confirmed_to_cancelled(self):
        "confirmed to canceled"
        b = make_booking(status=BookingStatus.CONFIRMED)
        b.cancel()
        assert b.status == BookingStatus.CANCELLED

    def test_confirmed_cannot_confirm_again(self):
        b = make_booking(status=BookingStatus.CONFIRMED)
        with pytest.raises(BookingStateError) as exc:
            b.confirm()
        assert exc.value.current_status   == "CONFIRMED"
        assert exc.value.attempted_action == "confirmed"

    def test_cancelled_is_terminal(self):
        b = make_booking(status=BookingStatus.CANCELLED)
        with pytest.raises(BookingStateError):
            b.cancel()

    def test_completed_is_terminal(self):
        b = make_booking(status=BookingStatus.COMPLETED)
        with pytest.raises(BookingStateError):
            b.complete()

    def test_pending_cannot_complete_directly(self):
        b = make_booking(status=BookingStatus.PENDING)
        with pytest.raises(BookingStateError):
            b.complete()


# ── Domain events ───────

class TestBookingDomainEvents:

    def test_confirm_emits_event(self):
        b = make_booking()
        b.confirm()
        events = b.pull_events()
        assert len(events) == 1
        assert events[0].event_type == "BookingConfirmed"
        assert events[0].payload["booking_id"] == b.id

    def test_cancel_emits_event(self):
        b = make_booking()
        b.cancel(reason="Annulation test")
        events = b.pull_events()
        assert len(events) == 1
        assert events[0].event_type == "BookingCancelled"
        assert events[0].payload["reason"] == "Annulation test"

    def test_complete_emits_event(self):
        b = make_booking(status=BookingStatus.CONFIRMED)
        b.complete()
        events = b.pull_events()
        assert any(e.event_type == "BookingCompleted" for e in events)

    def test_pull_events_clears_queue(self):
        b = make_booking()
        b.confirm()
        b.pull_events()  
        assert not b.has_pending_events()


# ── Règles métier ───────

class TestBookingBusinessRules:

    def test_is_cancellable_pending(self):
        assert make_booking(BookingStatus.PENDING).is_cancellable() is True

    def test_is_cancellable_confirmed(self):
        assert make_booking(BookingStatus.CONFIRMED).is_cancellable() is True

    def test_not_cancellable_completed(self):
        assert make_booking(BookingStatus.COMPLETED).is_cancellable() is False

    def test_free_cancellation_far_future(self):
        b = make_booking(days_until_checkin=10)
        assert b.is_free_cancellation(min_hours=48) is True

