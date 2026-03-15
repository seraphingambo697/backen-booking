"""manage_rooms.py — CRUD Rooms."""
from dataclasses import dataclass, field
from typing import List, Optional
from app.core.exceptions import AuthorizationError, EntityNotFoundError
from app.modules.hotel.domain.entities.hotel import Room, RoomType
from app.modules.hotel.domain.repositories.hotel_repository import HotelRepository, RoomRepository
from app.shared.domain.base_use_case import BaseUseCase


@dataclass
class CreateRoomInput:
    hotel_id:        str
    requester_id:    str
    name:            str
    type:            str
    description:     str
    price_per_night: float
    capacity:        int
    size_sqm:        int       = 25
    bed_count:       int       = 1
    bed_type:        str       = "Double"
    floor:           int       = 0
    amenities:       List[str] = field(default_factory=list)
    images:          List[str] = field(default_factory=list)


@dataclass
class GetRoomInput:
    room_id: str


@dataclass
class ListRoomsInput:
    hotel_id:       str
    available_only: bool = False


@dataclass
class UpdateRoomInput:
    room_id:         str
    requester_id:    str
    is_admin:        bool             = False
    name:            Optional[str]    = None
    price_per_night: Optional[float]  = None
    description:     Optional[str]    = None
    floor:           Optional[int]    = None
    amenities:       Optional[List[str]] = None
    images:          Optional[List[str]] = None
    is_available:    Optional[bool]   = None


class CreateRoomUseCase(BaseUseCase[CreateRoomInput, Room]):
    def __init__(self, room_repo: RoomRepository, hotel_repo: HotelRepository):
        self.room_repo  = room_repo
        self.hotel_repo = hotel_repo

    def execute(self, i: CreateRoomInput) -> Room:
        hotel = self.hotel_repo.find_by_id(i.hotel_id)
        if not hotel:
            raise EntityNotFoundError("Hotel", i.hotel_id)
        if not hotel.is_owned_by(i.requester_id):
            raise AuthorizationError("Vous n'êtes pas propriétaire de cet hôtel.")
        room = Room(
            hotel_id=i.hotel_id, name=i.name, type=RoomType(i.type),
            description=i.description, price_per_night=i.price_per_night,
            capacity=i.capacity, size_sqm=i.size_sqm, bed_count=i.bed_count,
            bed_type=i.bed_type, floor=i.floor,
            amenities=i.amenities, images=i.images,
        )
        return self.room_repo.save(room)


class GetRoomUseCase(BaseUseCase[GetRoomInput, Room]):
    def __init__(self, repository: RoomRepository):
        self.repository = repository

    def execute(self, i: GetRoomInput) -> Room:
        room = self.repository.find_by_id(i.room_id)
        if not room:
            raise EntityNotFoundError("Room", i.room_id)
        return room


class ListRoomsUseCase(BaseUseCase[ListRoomsInput, List[Room]]):
    def __init__(self, repository: RoomRepository):
        self.repository = repository

    def execute(self, i: ListRoomsInput) -> List[Room]:
        return self.repository.find_by_hotel(i.hotel_id, available_only=i.available_only)


class UpdateRoomUseCase(BaseUseCase[UpdateRoomInput, Room]):
    def __init__(self, repository: RoomRepository):
        self.repository = repository

    def execute(self, i: UpdateRoomInput) -> Room:
        room = self.repository.find_by_id(i.room_id)
        if not room:
            raise EntityNotFoundError("Room", i.room_id)
        for attr in ("name","price_per_night","description","floor","amenities","images","is_available"):
            val = getattr(i, attr)
            if val is not None:
                setattr(room, attr, val)
        room.touch()
        return self.repository.save(room)
