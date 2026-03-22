"""
app/modules/booking/domain/use_cases/create_booking.py
Création d'une réservation + vérification de disponibilité.

Utilise :
  - DateRange  → validation des dates, calcul des nuits
  - Money      → calcul du prix total
  - GuestCount → validation de la capacité
  - BookingConflictError → conflit de dates explicite
  - @transactional → atomicité de la sauvegarde
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from django.conf import settings

from app.core.exceptions import BookingConflictError, EntityNotFoundError, UnavailableError
from app.modules.booking.domain.entities.booking import Booking, BookingStatus
from app.modules.booking.domain.repositories.booking_repository import BookingRepository
from app.modules.hotel.domain.repositories.hotel_repository import RoomRepository
from app.shared.domain.base_use_case import BaseUseCase
from app.shared.domain.value_objects import DateRange, GuestCount, Money
from app.shared.infrastructure.database.transactional import transactional


@dataclass
class CreateBookingInput:
    user_id:          str
    hotel_id:         str
    room_id:          str
    check_in:         date
    check_out:        date
    guest_count:      int
    special_requests: str = ""
    adults:           int = 0  
    children:         int = 0


class CreateBookingUseCase(BaseUseCase[CreateBookingInput, Booking]):

    def __init__(self, booking_repo: BookingRepository, room_repo: RoomRepository):
        self.booking_repo = booking_repo
        self.room_repo    = room_repo

    @transactional
    def execute(self, i: CreateBookingInput) -> Booking:
        # check date 
        date_range = DateRange(check_in=i.check_in, check_out=i.check_out)

        max_nights = getattr(settings, "BOOKING_MAX_NIGHTS", 30)
        date_range.validate_max_nights(max_nights)

        # Valider les voyageurs 
        adults   = i.adults   if i.adults   > 0 else i.guest_count
        children = i.children if i.children > 0 else 0
        guests   = GuestCount(adults=adults, children=children)

        # Vérifier la chambre
        room = self.room_repo.find_by_id(i.room_id)
        if not room:
            raise EntityNotFoundError("Room", i.room_id)
        if not room.is_available:
            raise UnavailableError(f"La chambre '{room.name}' n'est plus disponible.")
        if not guests.fits_in(room.capacity):
            raise UnavailableError(
                f"La chambre '{room.name}' accepte au maximum {room.capacity} voyageur(s) "
                f"({guests.total} demandés)."
            )

        # ── 4. Détecter les conflits de dates 
        conflicts = self.booking_repo.find_by_room_and_dates(
            i.room_id, i.check_in, i.check_out
        )
        if conflicts:
            raise BookingConflictError(
                room_id      = i.room_id,
                check_in     = str(i.check_in),
                check_out    = str(i.check_out),
                conflict_ids = [b.id for b in conflicts],
            )

        # Calculer le prix 
        total = Money.from_price_per_night(
            price_per_night = room.price_per_night,
            nights          = date_range.nights,
            currency        = room.currency,
        )

        # Créer et persister
        booking = Booking(
            user_id          = i.user_id,
            hotel_id         = i.hotel_id,
            room_id          = i.room_id,
            date_range       = date_range,
            total            = total,
            guests           = guests,
            status           = BookingStatus.PENDING,
            special_requests = i.special_requests,
        )
        booking.collect_event("BookingCreated", {
            "booking_id": booking.id,
            "user_id":    i.user_id,
            "hotel_id":   i.hotel_id,
            "room_id":    i.room_id,
            "check_in":   str(i.check_in),
            "check_out":  str(i.check_out),
            "total":      total.amount,
            "currency":   total.currency,
            "nights":     date_range.nights,
        })

        return self.booking_repo.save(booking)
