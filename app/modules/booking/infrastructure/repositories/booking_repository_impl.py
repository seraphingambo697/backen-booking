"""
app/modules/booking/infrastructure/repositories/booking_repository_impl.py
Implémentation Django du BookingRepository.

Reconstruit les Value Objects (DateRange, Money, GuestCount) depuis
les champs plats du modèle ORM lors du mapping _to_entity().
"""
from __future__ import annotations

import logging
from datetime import date
from typing import List, Optional

from app.modules.booking.domain.entities.booking import Booking, BookingStatus
from app.modules.booking.domain.repositories.booking_repository import BookingRepository
from app.modules.booking.infrastructure.database.booking_models import BookingModel
from app.shared.domain.value_objects import DateRange, GuestCount, Money
from app.shared.infrastructure.database.base_repository_impl import BaseDjangoRepository

logger = logging.getLogger("app")


class DjangoBookingRepository(BaseDjangoRepository[Booking, BookingModel], BookingRepository):
    model_class = BookingModel
    entity_name = "Booking"

    # ── Requêtes spécialisées ─────────────────────────────────────────────────

    def find_by_user(
        self,
        user_id: str,
        status: Optional[BookingStatus] = None,
    ) -> List[Booking]:
        qs = BookingModel.objects.filter(user_id=user_id)
        if status:
            qs = qs.filter(status=status.value)
        return [self._to_entity(m) for m in qs]

    def find_by_hotel(
        self,
        hotel_id: str,
        status: Optional[BookingStatus] = None,
    ) -> List[Booking]:
        qs = BookingModel.objects.filter(hotel_id=hotel_id)
        if status:
            qs = qs.filter(status=status.value)
        return [self._to_entity(m) for m in qs]

    def find_by_room_and_dates(
        self,
        room_id:   str,
        check_in:  date,
        check_out: date,
    ) -> List[Booking]:
        """Réservations PENDING/CONFIRMED qui chevauchent la plage demandée."""
        qs = BookingModel.objects.filter(
            room_id   = room_id,
            status__in = ["CONFIRMED", "PENDING"],
            check_in__lt  = check_out,
            check_out__gt = check_in,
        )
        return [self._to_entity(m) for m in qs]

    def find_active_by_room(self, room_id: str) -> List[Booking]:
        qs = BookingModel.objects.filter(
            room_id    = room_id,
            status__in = ["CONFIRMED", "PENDING"],
        )
        return [self._to_entity(m) for m in qs]

    def find_by_status(self, status: BookingStatus) -> List[Booking]:
        return [
            self._to_entity(m)
            for m in BookingModel.objects.filter(status=status.value)
        ]

    def count_by_user(self, user_id: str) -> int:
        return BookingModel.objects.filter(user_id=user_id).count()

    # ── Mapping ORM → Entité ──────────────────────────────────────────────────

    def _to_entity(self, m: BookingModel) -> Booking:
        """
        Reconstruit l'entité Booking complète avec ses Value Objects.

        Stratégie pour DateRange : on contourne la validation 'check_in >= today'
        car les réservations existantes peuvent avoir des dates passées.
        """
        b = Booking.__new__(Booking)

        # Champs de base
        object.__setattr__(b, "id",         str(m.id))
        object.__setattr__(b, "user_id",    str(m.user_id))
        object.__setattr__(b, "hotel_id",   str(m.hotel_id))
        object.__setattr__(b, "room_id",    str(m.room_id))
        object.__setattr__(b, "status",     BookingStatus(m.status))
        object.__setattr__(b, "special_requests",    m.special_requests)
        object.__setattr__(b, "cancelled_at",        m.cancelled_at)
        object.__setattr__(b, "cancellation_reason", m.cancellation_reason)
        object.__setattr__(b, "created_at", m.created_at)
        object.__setattr__(b, "updated_at", m.updated_at)

        # DateRange — bypass validation pour les dates passées en base
        date_range = object.__new__(DateRange)
        object.__setattr__(date_range, "check_in",  m.check_in)
        object.__setattr__(date_range, "check_out", m.check_out)
        object.__setattr__(b, "date_range", date_range)

        # Money
        total = object.__new__(Money)
        object.__setattr__(total, "amount",   float(m.total_price))
        object.__setattr__(total, "currency", m.currency)
        object.__setattr__(b, "total", total)

        # GuestCount
        guests = object.__new__(GuestCount)
        object.__setattr__(guests, "adults",   m.adults)
        object.__setattr__(guests, "children", m.children)
        object.__setattr__(b, "guests", guests)

        # Initialiser la liste d'events (non persistée)
        object.__setattr__(b, "_events", [])

        return b

    # ── Mapping Entité → dict ORM ─────────────────────────────────────────────

    def _to_model_data(self, e: Booking) -> dict:
        return {
            "user_id":    e.user_id,
            "hotel_id":   e.hotel_id,
            "room_id":    e.room_id,
            # Dates depuis DateRange
            "check_in":   e.check_in,
            "check_out":  e.check_out,
            # Voyageurs depuis GuestCount
            "adults":     e.guests.adults   if e.guests else 1,
            "children":   e.guests.children if e.guests else 0,
            # Prix depuis Money
            "total_price": e.total.amount   if e.total else 0.0,
            "currency":    e.total.currency if e.total else "EUR",
            # Statut et divers
            "status":               e.status.value,
            "special_requests":     e.special_requests,
            "cancelled_at":         e.cancelled_at,
            "cancellation_reason":  e.cancellation_reason,
        }
