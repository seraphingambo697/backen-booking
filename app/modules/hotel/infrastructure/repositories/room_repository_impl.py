"""room_repository_impl.py"""
from datetime import date
from typing import List
from app.modules.hotel.domain.entities.hotel import Room, RoomType
from app.modules.hotel.domain.repositories.hotel_repository import RoomRepository
from app.modules.hotel.infrastructure.database.hotel_models import RoomModel
from app.shared.infrastructure.database.base_repository_impl import BaseDjangoRepository


class DjangoRoomRepository(BaseDjangoRepository[Room, RoomModel], RoomRepository):
    model_class = RoomModel
    entity_name = "Room"

    def find_by_hotel(self, hotel_id: str, available_only: bool = False) -> List[Room]:
        qs = RoomModel.objects.filter(hotel_id=hotel_id)
        if available_only:
            qs = qs.filter(is_available=True)
        return [self._to_entity(m) for m in qs.order_by("price_per_night")]

    def find_available_rooms(
        self, hotel_id: str, check_in: date, check_out: date, guest_count: int
    ) -> List[Room]:
        """Exclut les chambres avec une réservation confirmée ou pending chevauchante."""
        from app.modules.booking.infrastructure.database.booking_models import BookingModel
        booked_ids = BookingModel.objects.filter(
            room__hotel_id=hotel_id,
            status__in=["CONFIRMED", "PENDING"],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).values_list("room_id", flat=True)

        qs = RoomModel.objects.filter(
            hotel_id=hotel_id,
            is_available=True,
            capacity__gte=guest_count,
        ).exclude(id__in=booked_ids).order_by("price_per_night")

        return [self._to_entity(m) for m in qs]

    def find_by_type(self, hotel_id: str, room_type: str) -> List[Room]:
        qs = RoomModel.objects.filter(hotel_id=hotel_id, type=room_type, is_available=True)
        return [self._to_entity(m) for m in qs]

    # ── Mapping ORM ↔ Entité ─────────────────────────────────────────────────

    def _to_entity(self, m: RoomModel) -> Room:
        r = Room.__new__(Room)
        object.__setattr__(r, "id",              str(m.id))
        object.__setattr__(r, "hotel_id",        str(m.hotel_id))
        object.__setattr__(r, "name",            m.name)
        object.__setattr__(r, "type",            RoomType(m.type))
        object.__setattr__(r, "description",     m.description)
        object.__setattr__(r, "price_per_night", float(m.price_per_night))
        object.__setattr__(r, "currency",        m.currency)
        object.__setattr__(r, "capacity",        m.capacity)
        object.__setattr__(r, "size_sqm",        m.size_sqm)
        object.__setattr__(r, "bed_count",       m.bed_count)
        object.__setattr__(r, "bed_type",        m.bed_type)
        object.__setattr__(r, "floor",           m.floor)
        object.__setattr__(r, "amenities",       list(m.amenities))
        object.__setattr__(r, "images",          list(m.images))
        object.__setattr__(r, "is_available",    m.is_available)
        object.__setattr__(r, "created_at",      m.created_at)
        object.__setattr__(r, "updated_at",      m.updated_at)
        return r

    def _to_model_data(self, e: Room) -> dict:
        return {
            "hotel_id":        e.hotel_id,
            "name":            e.name,
            "type":            e.type.value,
            "description":     e.description,
            "price_per_night": e.price_per_night,
            "currency":        e.currency,
            "capacity":        e.capacity,
            "size_sqm":        e.size_sqm,
            "bed_count":       e.bed_count,
            "bed_type":        e.bed_type,
            "floor":           e.floor,
            "amenities":       e.amenities,
            "images":          e.images,
            "is_available":    e.is_available,
        }
