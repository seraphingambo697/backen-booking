"""
Entité Booking — logique métier pure
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from app.core.exceptions import BookingStateError
from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.value_objects import DateRange, GuestCount, Money



class BookingStatus(str, Enum):
    PENDING   = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

    def label(self) -> str:
        return {
            "PENDING":   "En attente",
            "CONFIRMED": "Confirmée",
            "CANCELLED": "Annulée",
            "COMPLETED": "Terminée",
        }[self.value]



# status valides
_VALID_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING:   {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED: {BookingStatus.CANCELLED, BookingStatus.COMPLETED},
    BookingStatus.CANCELLED: set(),
    BookingStatus.COMPLETED: set(),
}


# ── Entité 

@dataclass
class Booking(BaseEntity):
    """
    Réservation d'une chambre d'hôtel.
    Orchestre les transitions d'état et émet des domain events.
    """
    user_id:  str = ""
    hotel_id: str = ""
    room_id:  str = ""

    date_range: Optional[DateRange]  = None
    total:      Optional[Money]      = None
    guests:     Optional[GuestCount] = None

    status:              BookingStatus    = BookingStatus.PENDING
    special_requests:    str              = ""
    cancelled_at:        Optional[datetime] = None
    cancellation_reason: str              = ""

    # ── Propriétés calculées

    @property
    def check_in(self):
        return self.date_range.check_in if self.date_range else None

    @property
    def check_out(self):
        return self.date_range.check_out if self.date_range else None

    @property
    def nights(self) -> int:
        return self.date_range.nights if self.date_range else 0

    @property
    def guest_count(self) -> int:
        return self.guests.total if self.guests else 0

    @property
    def total_price(self) -> float:
        return self.total.amount if self.total else 0.0

    @property
    def currency(self) -> str:
        return self.total.currency if self.total else "EUR"

    # ── Machine à états ─

    def _transition(self, target: BookingStatus):
        allowed = _VALID_TRANSITIONS[self.status]
        if target not in allowed:
            raise BookingStateError(
                current_status=self.status.value,
                attempted_action=target.value.lower(),
            )
        self.status = target
        self.touch()

    def confirm(self):
        """PENDING → CONFIRMED. Appelé après paiement réussi."""
        self._transition(BookingStatus.CONFIRMED)
        self.collect_event("BookingConfirmed", {
            "booking_id": self.id,
            "user_id":    self.user_id,
            "hotel_id":   self.hotel_id,
            "check_in":   str(self.check_in),
            "check_out":  str(self.check_out),
            "total":      self.total_price,
            "currency":   self.currency,
        })

    def cancel(self, reason: str = ""):
        """PENDING|CONFIRMED → CANCELLED."""
        self._transition(BookingStatus.CANCELLED)
        self.cancelled_at        = datetime.utcnow()
        self.cancellation_reason = reason
        self.collect_event("BookingCancelled", {
            "booking_id": self.id,
            "user_id":    self.user_id,
            "reason":     reason,
        })

    def complete(self):
        """CONFIRMED → COMPLETED. Appelé au check-out."""
        self._transition(BookingStatus.COMPLETED)
        self.collect_event("BookingCompleted", {
            "booking_id": self.id,
            "user_id":    self.user_id,
            "hotel_id":   self.hotel_id,
        })

    # ── Règles métier ───

    def is_cancellable(self) -> bool:
        return self.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED)

    def is_free_cancellation(self, min_hours: int = 48) -> bool:
        if not self.date_range:
            return False
        return self.date_range.is_free_cancellation(min_hours)

    def belongs_to(self, user_id: str) -> bool:
        return self.user_id == user_id

    def __str__(self) -> str:
        return (
            f"Booking({self.id[:8]}… | {self.status.label()} | "
            f"{self.date_range} | {self.total})"
        )
