"""delete_hotel.py — Soft delete (status=INACTIVE)."""
from dataclasses import dataclass
from app.core.exceptions import AuthorizationError, EntityNotFoundError
from app.modules.hotel.domain.repositories.hotel_repository import HotelRepository
from app.shared.domain.base_use_case import BaseUseCase


@dataclass
class DeleteHotelInput:
    hotel_id:     str
    requester_id: str
    is_admin:     bool = False


class DeleteHotelUseCase(BaseUseCase[DeleteHotelInput, None]):
    def __init__(self, repository: HotelRepository):
        self.repository = repository

    def execute(self, i: DeleteHotelInput) -> None:
        hotel = self.repository.find_by_id(i.hotel_id)
        if not hotel:
            raise EntityNotFoundError("Hotel", i.hotel_id)
        if not hotel.is_owned_by(i.requester_id) and not i.is_admin:
            raise AuthorizationError("Vous n'êtes pas propriétaire de cet hôtel.")
        hotel.deactivate()
        self.repository.save(hotel)
