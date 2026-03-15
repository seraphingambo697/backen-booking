"""hotel_repository_impl.py"""
from typing import List, Optional
from app.modules.hotel.domain.entities.hotel import Hotel, HotelStatus
from app.modules.hotel.domain.repositories.hotel_repository import HotelRepository
from app.modules.hotel.infrastructure.database.hotel_models import HotelModel
from app.shared.infrastructure.database.base_repository_impl import BaseDjangoRepository


class DjangoHotelRepository(BaseDjangoRepository[Hotel, HotelModel], HotelRepository):
    model_class = HotelModel
    entity_name = "Hotel"

    # ── Requêtes spécialisées ─────────────────────────────────────────────────

    def find_all(self, city: Optional[str] = None, active_only: bool = True) -> List[Hotel]:
        qs = HotelModel.objects.all()
        if active_only:
            qs = qs.filter(status="ACTIVE")
        if city:
            qs = qs.filter(city__icontains=city)
        return [self._to_entity(m) for m in qs]

    def find_by_city(self, city: str) -> List[Hotel]:
        qs = HotelModel.objects.filter(city__icontains=city, status="ACTIVE")
        return [self._to_entity(m) for m in qs]

    def find_by_owner(self, owner_id: str) -> List[Hotel]:
        return [self._to_entity(m) for m in HotelModel.objects.filter(owner_id=owner_id)]

    def search(
        self,
        city:        str,
        stars_min:   Optional[int]       = None,
        amenities:   Optional[List[str]] = None,
        active_only: bool                = True,
    ) -> List[Hotel]:
        qs = HotelModel.objects.filter(city__icontains=city)
        if active_only:
            qs = qs.filter(status="ACTIVE")
        if stars_min:
            qs = qs.filter(stars__gte=stars_min)
        hotels = [self._to_entity(m) for m in qs]
        # Filtre amenities en Python (JSON array — pas de support natif SQLite)
        if amenities:
            hotels = [h for h in hotels if all(a in h.amenities for a in amenities)]
        return hotels

    # ── Mapping ORM ↔ Entité ─────────────────────────────────────────────────

    def _to_entity(self, m: HotelModel) -> Hotel:
        h = Hotel.__new__(Hotel)
        object.__setattr__(h, "id",          str(m.id))
        object.__setattr__(h, "owner_id",    str(m.owner_id) if m.owner_id else "")
        object.__setattr__(h, "name",        m.name)
        object.__setattr__(h, "description", m.description)
        object.__setattr__(h, "address",     m.address)
        object.__setattr__(h, "city",        m.city)
        object.__setattr__(h, "country",     m.country)
        object.__setattr__(h, "latitude",    m.latitude)
        object.__setattr__(h, "longitude",   m.longitude)
        object.__setattr__(h, "stars",       m.stars)
        object.__setattr__(h, "status",      HotelStatus(m.status))
        object.__setattr__(h, "phone",       m.phone)
        object.__setattr__(h, "email",       m.email)
        object.__setattr__(h, "website",     m.website)
        object.__setattr__(h, "amenities",   list(m.amenities))
        object.__setattr__(h, "images",      list(m.images))
        object.__setattr__(h, "created_at",  m.created_at)
        object.__setattr__(h, "updated_at",  m.updated_at)
        return h

    def _to_model_data(self, e: Hotel) -> dict:
        return {
            "owner_id":    e.owner_id or None,
            "name":        e.name,
            "description": e.description,
            "address":     e.address,
            "city":        e.city,
            "country":     e.country,
            "latitude":    e.latitude,
            "longitude":   e.longitude,
            "stars":       e.stars,
            "status":      e.status.value,
            "phone":       e.phone,
            "email":       e.email,
            "website":     e.website,
            "amenities":   e.amenities,
            "images":      e.images,
        }
