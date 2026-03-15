"""
Tests unitaires use cases Booking — repositories mockés.
pytest app/modules/booking/tests/unit/ -v
"""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import (
    AuthorizationError,
    BookingConflictError,
    EntityNotFoundError,
    UnavailableError,
)
from app.modules.booking.domain.entities.booking import Booking, BookingStatus
from app.modules.booking.domain.use_cases.cancel_booking    import CancelBookingInput, CancelBookingUseCase
from app.modules.booking.domain.use_cases.check_availability import CheckAvailabilityInput, CheckAvailabilityUseCase
from app.modules.booking.domain.use_cases.complete_booking  import CompleteBookingInput, CompleteBookingUseCase
from app.modules.booking.domain.use_cases.confirm_booking   import ConfirmBookingInput, ConfirmBookingUseCase
from app.modules.booking.domain.use_cases.create_booking    import CreateBookingInput, CreateBookingUseCase
from app.modules.booking.domain.use_cases.get_booking       import GetBookingInput, GetBookingUseCase, ListBookingsInput, ListBookingsUseCase
from app.modules.hotel.domain.entities.hotel import Room, RoomType
from app.shared.domain.value_objects import DateRange, GuestCount, Money


# ── Factories ───────────

def _booking(status=BookingStatus.PENDING, user_id="uid-1", **kw) -> Booking:
    b = Booking.__new__(Booking)
    ci = date.today() + timedelta(days=10)
    co = ci + timedelta(days=3)
    dr = object.__new__(DateRange)
    object.__setattr__(dr, "check_in", ci)
    object.__setattr__(dr, "check_out", co)
    money = object.__new__(Money)
    object.__setattr__(money, "amount", 450.0)
    object.__setattr__(money, "currency", "EUR")
    guests = object.__new__(GuestCount)
    object.__setattr__(guests, "adults", 2)
    object.__setattr__(guests, "children", 0)
    attrs = dict(
        id="bid-1", user_id=user_id, hotel_id="hid-1", room_id="rid-1",
        status=status, date_range=dr, total=money, guests=guests,
        special_requests="", cancelled_at=None, cancellation_reason="",
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(), _events=[],
    )
    attrs.update(kw)
    for k, v in attrs.items():
        object.__setattr__(b, k, v)
    return b


def _room(available=True, capacity=4) -> Room:
    r = Room.__new__(Room)
    attrs = dict(
        id="rid-1", hotel_id="hid-1", name="Suite", type=RoomType.SUITE,
        description="", price_per_night=150.0, currency="EUR",
        capacity=capacity, size_sqm=50, bed_count=1, bed_type="King",
        floor=3, amenities=[], images=[], is_available=available,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    for k, v in attrs.items():
        object.__setattr__(r, k, v)
    return r


# ── CreateBookingUseCase 

class TestCreateBookingUseCase:

    def _uc(self, room=None, conflicts=None):
        booking_repo = MagicMock()
        room_repo    = MagicMock()
        booking_repo.find_by_room_and_dates.return_value = conflicts or []
        booking_repo.save.side_effect = lambda b: b
        room_repo.find_by_id.return_value = room or _room()
        return CreateBookingUseCase(booking_repo, room_repo), booking_repo, room_repo

    def _input(self, **kw):
        defaults = dict(
            user_id="uid-1", hotel_id="hid-1", room_id="rid-1",
            check_in=date.today() + timedelta(days=5),
            check_out=date.today() + timedelta(days=8),
            guest_count=2,
        )
        defaults.update(kw)
        return CreateBookingInput(**defaults)

    @patch("app.modules.booking.domain.use_cases.create_booking.transaction.atomic")
    def test_creates_booking_successfully(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        uc, repo, _ = self._uc()
        result = uc.execute(self._input())
        assert result.status  == BookingStatus.PENDING
        assert result.user_id == "uid-1"
        repo.save.assert_called_once()

    @patch("app.modules.booking.domain.use_cases.create_booking.transaction.atomic")
    def test_raises_if_room_not_found(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        uc, _, room_repo = self._uc()
        room_repo.find_by_id.return_value = None
        with pytest.raises(EntityNotFoundError) as exc:
            uc.execute(self._input())
        assert exc.value.entity == "Room"

    @patch("app.modules.booking.domain.use_cases.create_booking.transaction.atomic")
    def test_raises_if_room_unavailable(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        uc, _, _ = self._uc(room=_room(available=False))
        with pytest.raises(UnavailableError):
            uc.execute(self._input())

    @patch("app.modules.booking.domain.use_cases.create_booking.transaction.atomic")
    def test_raises_if_capacity_exceeded(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        uc, _, _ = self._uc(room=_room(capacity=1))
        with pytest.raises(UnavailableError):
            uc.execute(self._input(guest_count=3))

    @patch("app.modules.booking.domain.use_cases.create_booking.transaction.atomic")
    def test_raises_on_date_conflict(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        existing = _booking()
        uc, _, _ = self._uc(conflicts=[existing])
        with pytest.raises(BookingConflictError) as exc:
            uc.execute(self._input())
        assert exc.value.room_id == "rid-1"
        assert "bid-1" in exc.value.conflict_ids

    @patch("app.modules.booking.domain.use_cases.create_booking.transaction.atomic")
    def test_total_price_calculated(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        uc, _, _ = self._uc(room=_room())
        result = uc.execute(self._input(
            check_in=date.today() + timedelta(days=5),
            check_out=date.today() + timedelta(days=8),  # 3 nuits × 150€
        ))
        assert result.total_price == 450.0


# ── GetBookingUseCase ───

class TestGetBookingUseCase:

    def test_returns_booking_for_owner(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _booking(user_id="uid-1")
        uc = GetBookingUseCase(repo)
        result = uc.execute(GetBookingInput(booking_id="bid-1", requester_id="uid-1"))
        assert result.id == "bid-1"

    def test_admin_can_access_any_booking(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _booking(user_id="uid-1")
        uc = GetBookingUseCase(repo)
        result = uc.execute(GetBookingInput(booking_id="bid-1", requester_id="admin", is_admin=True))
        assert result.id == "bid-1"

    def test_raises_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        uc = GetBookingUseCase(repo)
        with pytest.raises(EntityNotFoundError):
            uc.execute(GetBookingInput(booking_id="ghost", requester_id="uid-1"))

    def test_raises_authorization_for_stranger(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _booking(user_id="uid-1")
        uc = GetBookingUseCase(repo)
        with pytest.raises(AuthorizationError):
            uc.execute(GetBookingInput(booking_id="bid-1", requester_id="stranger"))


# ── CancelBookingUseCase 

class TestCancelBookingUseCase:

    @patch("app.modules.booking.domain.use_cases.cancel_booking.transaction.atomic")
    def test_owner_can_cancel(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        repo = MagicMock()
        booking = _booking(user_id="uid-1")
        repo.find_by_id.return_value = booking
        repo.save.side_effect = lambda b: b
        uc = CancelBookingUseCase(repo)
        result = uc.execute(CancelBookingInput(booking_id="bid-1", requester_id="uid-1", reason="Test"))
        assert result.booking.status == BookingStatus.CANCELLED

    @patch("app.modules.booking.domain.use_cases.cancel_booking.transaction.atomic")
    def test_stranger_cannot_cancel(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        repo = MagicMock()
        repo.find_by_id.return_value = _booking(user_id="uid-1")
        uc = CancelBookingUseCase(repo)
        with pytest.raises(AuthorizationError):
            uc.execute(CancelBookingInput(booking_id="bid-1", requester_id="stranger"))

    @patch("app.modules.booking.domain.use_cases.cancel_booking.transaction.atomic")
    def test_free_cancellation_far_future(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        repo = MagicMock()
        repo.find_by_id.return_value = _booking(user_id="uid-1")
        repo.save.side_effect = lambda b: b
        uc = CancelBookingUseCase(repo)
        result = uc.execute(CancelBookingInput(booking_id="bid-1", requester_id="uid-1"))
        assert result.is_free is True
        assert result.refund_amount == 450.0


# ── ConfirmBookingUseCase ─────────────────────────────────────────────────────

class TestConfirmBookingUseCase:

    @patch("app.modules.booking.domain.use_cases.confirm_booking.transaction.atomic")
    def test_confirm_pending_booking(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        repo = MagicMock()
        repo.find_by_id.return_value = _booking()
        repo.save.side_effect = lambda b: b
        uc = ConfirmBookingUseCase(repo)
        result = uc.execute(ConfirmBookingInput(booking_id="bid-1", requester_id="uid-1"))
        assert result.status == BookingStatus.CONFIRMED

    @patch("app.modules.booking.domain.use_cases.confirm_booking.transaction.atomic")
    def test_admin_can_confirm_any(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        repo = MagicMock()
        repo.find_by_id.return_value = _booking(user_id="uid-1")
        repo.save.side_effect = lambda b: b
        uc = ConfirmBookingUseCase(repo)
        result = uc.execute(ConfirmBookingInput(booking_id="bid-1", requester_id="admin", is_admin=True))
        assert result.status == BookingStatus.CONFIRMED


# ── CompleteBookingUseCase ────────────────────────────────────────────────────

class TestCompleteBookingUseCase:

    @patch("app.modules.booking.domain.use_cases.complete_booking.transaction.atomic")
    def test_complete_confirmed_booking(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        repo = MagicMock()
        repo.find_by_id.return_value = _booking(status=BookingStatus.CONFIRMED)
        repo.save.side_effect = lambda b: b
        uc = CompleteBookingUseCase(repo)
        result = uc.execute(CompleteBookingInput(booking_id="bid-1"))
        assert result.status == BookingStatus.COMPLETED

    @patch("app.modules.booking.domain.use_cases.complete_booking.transaction.atomic")
    def test_raises_not_found(self, mock_atomic):
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__  = MagicMock(return_value=False)
        repo = MagicMock()
        repo.find_by_id.return_value = None
        uc = CompleteBookingUseCase(repo)
        with pytest.raises(EntityNotFoundError):
            uc.execute(CompleteBookingInput(booking_id="ghost"))


# ── CheckAvailabilityUseCase ──────────────────────────────────────────────────

class TestCheckAvailabilityUseCase:

    def test_returns_available_rooms(self):
        booking_repo = MagicMock()
        room_repo    = MagicMock()
        room_repo.find_available_rooms.return_value = [_room(), _room()]
        uc = CheckAvailabilityUseCase(booking_repo, room_repo)
        results = uc.execute(CheckAvailabilityInput(
            hotel_id    = "hid-1",
            check_in    = date.today() + timedelta(days=5),
            check_out   = date.today() + timedelta(days=8),
            guest_count = 2,
        ))
        assert len(results) == 2
        assert results[0].nights      == 3
        assert results[0].total_price == 450.0  # 150 × 3

    def test_returns_empty_if_no_rooms(self):
        booking_repo = MagicMock()
        room_repo    = MagicMock()
        room_repo.find_available_rooms.return_value = []
        uc = CheckAvailabilityUseCase(booking_repo, room_repo)
        results = uc.execute(CheckAvailabilityInput(
            hotel_id    = "hid-1",
            check_in    = date.today() + timedelta(days=5),
            check_out   = date.today() + timedelta(days=7),
            guest_count = 2,
        ))
        assert results == []
